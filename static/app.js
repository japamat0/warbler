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
        console.log(res);
        
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
        console.log(e.target);
        
        //post request to like end point
        $.ajax({
            type: "POST",
            url: `/users/follow/${followee_id}`,
            success: handleFollow
        })
    })
})







