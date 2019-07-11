$(function() {
  function handleMessageDelete(res) {
    //remove li from dom
    $(`#msg-${res}`).remove();
  }

  function handleLikeMessage(res) {
    $(`#like-${res.msgId}`).toggleClass('fas far');
    $(`#${res.msgId}-num-likes`).text(`${res.likes}`);
  }

  function handleFollow(res) {
    let text = res.isFollowing === true ? 'Unfollow' : 'Follow';
    $(`#user-${res.followeeId}`).text(text);
    $(`#user-${res.followeeId}`).toggleClass('btn-outline-primary btn-primary');
  }

  function populateModal(res) {
    // select modal, change content
    $('#commentModalTitle').text(res.username);
    $('.modal-body').text(res.text);
    $('#msg-comments').empty();
    $('#message-id').val(res.id);
    
    
    if (res.comments.length) {
      for (let comment of res.comments) {
        let formattedComment = makeHtml(comment);
        $('#msg-comments').append(formattedComment);
      }
    } else {
      let noComments = `<p class="empty-comments"><small><em>No comments to show</em></small></p>`;
      $('#msg-comments').append(noComments);
    }
  }

  function makeHtml(obj) {
    return `
      <div class="card m-2">
        <div class="card-body">
          <p>${obj.text}</p>
          <div class="d-flex align-items-center">
            <a href="/users/${obj.user_id}">
              <img src="${ obj.image_url }" alt="${obj.username}" class="timeline-image user-cmnt-badge mr-3"/>
            </a>
            <a href="/users/${obj.user_id}">@${obj.username}</a>
            <cite class="ml-3" title="Source Title">${obj.timestamp.slice(0,16)}</cite>
          </div>
        </div>
      </div>`;
  }

  function handleCommentSuccess(res) {
    $('#commentModalLong').modal('hide');
    $('#comment-form').trigger('reset');
    let numComments = parseInt($(`#${res.msg_id}-num-comments`).text()) + 1;
    $(`#${res.msg_id}-num-comments`).text(numComments);
  }

  function handleCommentError(res) {
    let text = $('#comment-text').val();
    
    let msg = text.length
      ? 'Comments must be less than 140 characters'
      : 'Comments cannot be blank';
    
    $('#comment-error').text(msg);
    $('#comment-error').addClass('error-fade');
    setTimeout(()=> {
      $('#comment-error').empty();
      $('#comment-error').removeClass('error-fade');
    }, 3000);
  }

  $('[data-toggle="tooltip"]').tooltip();

  $('.trash-btn').on('click', (e) => {
    e.preventDefault();

    //get message_id
    const msg_id = e.target.getAttribute('data-msg');

    //post request to delete end point
    $.ajax({
      type: 'POST',
      url: `/messages/${msg_id}/delete`,
      success: handleMessageDelete
    });
  });

  $('.like-btn').on('click', (e) => {
    e.preventDefault();
    //get message_id
    const msg_id = e.target.getAttribute('data-msg');

    const data = {
      'msg-id': msg_id
    };

    //post request to like end point
    $.ajax({
      type: 'POST',
      url: `/like`,
      data: JSON.stringify(data),
      contentType: 'application/json',
      success: handleLikeMessage
    });
  });

  $('.follow-btn').on('click', (e) => {
    e.preventDefault();

    const followee_id = e.target.getAttribute('data-msg');

    //post request to like end point
    $.ajax({
      type: 'POST',
      url: `/users/follow/${followee_id}`,
      success: handleFollow
    });
  });

  // button to populate message info
  $('.comment-btn').on('click', (e) => {
    e.preventDefault();
    const msg_id = e.target.type === 'button'
      ? $(e.target).children()[0].getAttribute('data-msg')
      :  e.target.getAttribute('data-msg');
    
    $.ajax({
      type: 'POST',
      url: `/messages/${msg_id}`,
      success: populateModal
    });
  });

  // button in modal to create comment
  $('#add-comment-btn').on('click', (e) => {
    e.preventDefault();

    let text = $('#comment-text').val();
    let data = {
      text: text.length ? text : null,
      msgId: $('#message-id').val()
    };

    $.ajax({
      type: 'POST',
      url: `/messages/comments`,
      data: JSON.stringify(data),
      contentType: 'application/json',
      success: handleCommentSuccess,
      error: handleCommentError
    });
  });
});
