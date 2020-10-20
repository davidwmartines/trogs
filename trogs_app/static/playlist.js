$(() => {
  const firstTrackId = "track_0";
  const lastTrackId = `track_${$("audio").length - 1}`;

  let currentTrackId = firstTrackId;

  const buttonPlaying = () => {
    $("#playpause").prop("checked", false)
      .next().attr('title', 'Stop');
  };

  const buttonPaused = () => {
    $("#playpause").prop("checked", true)
      .next().attr('title', 'Play');
  };

  const getNextTrackId = (current) => {
    const currentIndex = parseInt(current.split("_")[1]);
    const nextIndex = currentIndex + 1;
    return `track_${nextIndex}`;
  };

  buttonPaused();

  currentTrackId = firstTrackId;

  // any time a track starts playing
  $("audio").on("play", (e) => {
    buttonPlaying();
    currentTrackId = e.target.id;

    $(e.target).focus();
    $(e.target).parent().parent().addClass("currenttrack");

    // turn of all other tracks
    // note: need to use "function" syntax for proper "this" handling.
    $("audio").each(function () {
      const audio = this;
      if (audio.id !== currentTrackId) {
        audio.pause();
        $(audio).parent().parent().removeClass("currenttrack");
      }
    });
  });

  // any time a track pauses
  $("audio").on("pause", (e) => {
    // set button to paused if current track is pausing.
    if (e.target.id === currentTrackId) {
      buttonPaused();
    }
  });

  // when a track ends
  $("audio").on("ended", (e) => {
    $(e.target).parent().parent().removeClass("currenttrack");

    // queue up next track
    if (e.target.id !== lastTrackId) {
      currentTrackId = getNextTrackId(currentTrackId);
    }

    // queue up first track again
    if (e.target.id === lastTrackId) {
      currentTrackId = firstTrackId;
    }

    // play next
    const currentAudio = $(`#${currentTrackId}`)[0];
    currentAudio.currentTime = 0;
    currentAudio.play();
  });

  // try to start playing selected track!
  if ($(`#${currentTrackId}`).length) {
    $(`#${currentTrackId}`)[0]
      .play()
      .catch((e) => console.log(e.toString()));
  }

  // main button cick handler
  $("#playpause").on("click", (e) => {
    //console.log("track", currentTrackId);
    const audio = $(`#${currentTrackId}`)[0];
    if (e.target.checked) {
      audio.pause();
    } else {
      audio.play();
    }
  });
});
