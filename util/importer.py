from . import admin
import os
import pyodbc


def get_conn():
    return pyodbc.connect(os.environ["MUSHMUD_SQL"])


def list_artists():
    conn = get_conn()
    cursor = conn.cursor()
    with cursor.execute("""SELECT
    a.id, a.name, p.username, am.email
    FROM mc.artist a
    JOIN mc.artistperson ap on ap.artistid = a.id
    JOIN mc.person p ON p.id = ap.personid
    JOIN dbo.aspnet_users u ON u.username = p.username
    JOIN dbo.aspnet_membership am on am.userid = u.userid
    WHERE a.id IN (SELECT artistid FROM mc.work 
        WHERE worktype ='audio'
    )"""):
        row = cursor.fetchone()
        while row:
            print(row)
            row = cursor.fetchone()


def list_albums(artist_id):
    conn = get_conn()
    cursor = conn.cursor()
    with cursor.execute("""SELECT 
    w.id, w.name, w.releasedate, l.abbreviation as license, 
    b.fileformat, b.binaryfiledataid  
    FROM mc.work w
    LEFT JOIN mc.binaryfileinfo b ON b.id = w.binaryfileinfoid
    LEFT JOIN mc.License l ON w.LicenseId = l.Id
    WHERE w.artistid = ? AND w.worktype ='collection'""", artist_id):
        row = cursor.fetchone()
        while row:
            yield row
            row = cursor.fetchone()


def list_tracks(album_id):
    conn = get_conn()
    cursor = conn.cursor()
    with cursor.execute("""SELECT
    w.id, w.name, b.binaryfiledataid,
    a.name,
    ww.name
    FROM mc.work w 
    JOIN mc.binaryfileinfo b ON w.binaryfileinfoid = b.id 
    JOIN mc.artist a on a.id = w.artistid
    JOIN (SELECT id, name FROM mc.work WHERE id = ?) ww ON ww.id = w.parentworkid
    WHERE w.parentworkid = ? AND w.worktype ='audio'
    ORDER BY w.ViewOrder""", album_id, album_id):
        row = cursor.fetchone()
        while row:
            yield {
                'title': row[1],
                'fileId': row[2],
                'albumTitle': row[4],
                'artistName': row[3]
            }
            row = cursor.fetchone()


def list_singles(artist_id):
    conn = get_conn()
    cursor = conn.cursor()
    with cursor.execute("""SELECT 
    w.id, w.name, 
    l.abbreviation as license,
    b.fileformat, b.binaryfiledataid 
    FROM mc.work w 
    JOIN mc.binaryfileinfo b ON w.binaryfileinfoid = b.id
    LEFT JOIN mc.License l ON w.LicenseId = l.Id
    WHERE w.artistid = ? AND w.parentworkid IS NULL AND w.worktype ='audio'""", artist_id):
        row = cursor.fetchone()
        while row:
            print(row)
            row = cursor.fetchone()


def get_file(id, file_name):
    conn = get_conn()
    cursor = conn.cursor()
    with cursor.execute("SELECT [Data] FROM mc.BinaryFileData WHERE Id = ?", id):
        row = cursor.fetchone()
        data = row[0]
    with open(file_name, 'wb') as file:
        file.write(data)


def import_artist(id):
    print("getting data for artist id '{0}'".format(id))
    conn = get_conn()
    cursor = conn.cursor()
    with cursor.execute("""
        SELECT
        a.id, a.name, a.bio,
        p.username, am.email,
        b.fileformat, b.binaryfiledataid 
        FROM mc.artist a
        JOIN mc.artistperson ap on ap.artistid = a.id
        JOIN mc.person p ON p.id = ap.personid
        JOIN dbo.aspnet_users u ON u.username = p.username
        JOIN dbo.aspnet_membership am on am.userid = u.userid
        LEFT JOIN mc.binaryfileinfo b ON b.id = a.binaryfileinfoid
        WHERE a.id =?""", id):
        data = cursor.fetchone()

    artist_name = data[1]
    artist_bio = data[2]
    artist_owner = data[4]
    imageid = data[6]
    print("got data for '{0}'".format(artist_name))

    imageUrl = ''
    if(imageid != ''):
        filename = "temp.jpg"
        print('downloading image data...')
        get_file(imageid, filename)
        print("created file '{0}'".format(filename))

        object_name = 'art/{0}/{0}.jpg'.format(
            admin.safe_obj_name(artist_name))
        full_url = admin.save_to_s3('temp.jpg', object_name, 'image/jpeg')
        print(full_url)
        # use the s3 object path for ImageURL
        imageUrl = object_name

    admin.create_artist(artist_name, artist_owner, artist_bio, imageUrl)


def import_album(id, conn=None):
    print("getting data for album id '{0}'".format(id))
    if (conn is None):
        conn = get_conn()
    
    cursor = conn.cursor()
    with cursor.execute("""
        SELECT
            w.name,
            w.releasedate,
            w.description,
            l.abbreviation as license, 
            b.binaryfiledataid,
            a.name as artistName
        FROM mc.work w
        LEFT JOIN mc.binaryfileinfo b ON b.id = w.binaryfileinfoid
        LEFT JOIN mc.License l ON w.LicenseId = l.Id
        JOIN mc.Artist a ON a.id = w.ArtistId
        WHERE w.id = ?""", id):
        data = cursor.fetchone()
    
    title = data[0]
    releaseDate = data[1].strftime("%Y-%m-%d")
    description = data[2]
    license = data[3]
    imageId = data[4]
    artistName = data[5]

    print("got data for '{0}'".format(title))

    imageUrl = ''
    if(imageId != ''):
        filename = "temp.jpg"
        print('downloading image data...')
        get_file(imageId, filename)
        print("created file '{0}'".format(filename))

        object_name = 'art/{0}/{1}/{1}.jpg'.format(
            admin.safe_obj_name(artistName), admin.safe_obj_name(title))
        full_url = admin.save_to_s3('temp.jpg', object_name, 'image/jpeg')
        print(full_url)
        # use the s3 object path for ImageURL
        imageUrl = object_name

    admin.create_album(artistName, title, releaseDate, license, description, imageUrl)

    import_tracks(id)


def import_tracks(album_id):
    track_list = list_tracks(album_id)
    for track in track_list:
        import_track(track)


def import_track(track):
    print('importing track {0}'.format(track['title']))

    print('downloading audio data...')
    filename = "temp.mp3"
    get_file(track['fileId'], filename)
    print("created file '{0}'".format(filename))

    object_name = 'art/{0}/{1}/{2}.mp3'.format(
        admin.safe_obj_name(track['artistName']),
        admin.safe_obj_name(track['albumTitle']),
        admin.safe_obj_name(track['title']))
    full_url = admin.save_to_s3('temp.mp3', object_name, 'audio/mpeg')
    print(full_url)

    admin.add_track(track['artistName'], track['albumTitle'], track['title'], full_url)