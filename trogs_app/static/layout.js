$(() => {
  const clipboard = new ClipboardJS(".share");
  $(".share").attr("data-clipboard-text", function (i, val) {
    return location.protocol + "//" + location.host + val;
  });

  $(".share").click(function (e) {
    e.preventDefault();
  });

  clipboard.on("success", function (e) {
      $(e.trigger).append($('<span class="copied">Link Copied!</span>')
        .fadeOut(3000).remove()
      );
      console.log(e.text);
  });
});
