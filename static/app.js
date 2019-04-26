$(function () {
    function handleMessageDelete(res) {
        //remove li from dom
        $(`#msg-${res}`).remove()
    }
    
    function handleLikeMessage(res) {
        $(`#like-${res.msgId}`).toggleClass("fas far")
        $(`#${res.msgId}-num-likes`).text(`${res.likes}`)
    }
    
    function handleFollow(res) {
        let text = res.isFollowing === true ? 'Unfollow' : 'Follow'
        $(`#user-${res.followeeId}`).text(text)
        $(`#user-${res.followeeId}`).toggleClass("btn-outline-primary btn-primary")
    }

    function populateModal(res) {

        // select modal, change content
        $('#commentModalTitle').text(res.username)
        $('.modal-body').text(res.text)
        hiddenInput = `<input type="hidden" id="message-id" name="message-${res.id}" value="${res.id}">`
        $('#comment-form').append(hiddenInput)
    }

    function handleCommentSuccess(res) {
        $('#commentModalLong').modal('hide')        
        $('#comment-form').trigger('reset')
    }


    $('[data-toggle="tooltip"]').tooltip()

    // hook up delete button 
    $('.trash-btn').on('click', (e) => {
        e.preventDefault()

        //get message_id
        msg_id = e.target.getAttribute('data-msg')
        
        //post request to delete end point
        $.ajax({
            type: "POST",
            url: `/messages/${msg_id}/delete`,
            success: handleMessageDelete
        })
    })
    
    $('.like-btn').on('click', (e) => {
        e.preventDefault()
        
        //get message_id
        msg_id = e.target.getAttribute('data-msg')
        
        data = {
            "msg-id": msg_id
        }
        
        //post request to like end point
        $.ajax({
            type: "POST",
            url: `/like`,
            data: JSON.stringify(data),
            contentType: "application/json",
            success: handleLikeMessage
        })
    })
    
    $('.follow-btn').on('click', (e) => {
        e.preventDefault()
        
        followee_id = e.target.getAttribute('data-msg')
        
        //post request to like end point
        $.ajax({
            type: "POST",
            url: `/users/follow/${followee_id}`,
            success: handleFollow
        })
    })
    
    // button to populate message info
    $('.comment-btn').on('click', (e) => {
        e.preventDefault()
        
        msg_id = e.target.getAttribute('data-msg')
        console.log(msg_id);
        
        $.ajax({
            type: "POST",
            url: `/messages/${msg_id}`,
            success: populateModal
        })
        
    })

    // button in modal to create comment
    $('#add-comment-btn').on('click', (e) => {
        e.preventDefault()

        let thing = $('#message-id').val()
        console.log(thing);
        
        let data = {
            text: $('#comment-text').val(),
            msgId: $('#message-id').val(),
        }

        $.ajax({
            type: "POST",
            url: `/messages/comments`,
            data: JSON.stringify(data),
            contentType: "application/json",
            success: handleCommentSuccess
        })
        
    })
})







