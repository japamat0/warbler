$(function () {
    function handleMessageDelete(res) {

        //remove li from dom
        $(`#msg-${res}`).remove()
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
})







