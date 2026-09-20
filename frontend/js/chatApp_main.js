const $ = document.querySelector.bind(document)

const LOGIN_STORAGE_KEY = 'CHAT_WATCH_LOGIN'
const API_URL =
    window.CHAT_WATCH_API_URL ||
    (
        window.location.port === '5000'
            ? window.location.origin
            : `${window.location.protocol}//${window.location.hostname}:5000`
    )

const SOCKET_URL = API_URL

const userName = $('#user_name')
const userAvt = $('#user_avt')
const profileName = $('#profile_name')
const profileUserId = $('#profileUserId')
const copyUserId = $('#copyUserId')

const logoutBtn = $('#logout')
const profileBtn = $('#profile')
const userPassword = $('#userPassword')

const logoutModal = $('#logoutModal')
const profileModal = $('#profileModal')
const passwordModal = $('#passwordModal')

const closeLogout = $('#close')
const cancelLogout = $('#cancelLogout')
const agreeLogout = $('#agree')

const closeProfile = $('#closeProfile')
const cancelProfile = $('#cancelProfile')
const saveProfile = $('#saveProfile')

const closePassword = $('#closePassword')
const cancelPassword = $('#cancelPassword')
const savePassword = $('#savePassword')

const avatarInput = $('#avatar_input')
const profileAvt = $('#profile_avt')

const currentPassword = $('#currentPassword')
const newPassword = $('#newPassword')
const confirmPassword = $('#confirmPassword')

const passwordInputs = [
    currentPassword,
    newPassword,
    confirmPassword
]
const addFriendBtns = document.querySelectorAll('#addFriendBtn')
const addfrModal = $('#addfrModal')
const closeAddFriend = $('#closeAddFriend')

const friendUserSearch = $('#friendUserSearch')
const searchFriendBtn = $('#searchFriendBtn')
const friendSearchResult = $('#friendSearchResult')

const notificationIcon = $('#notification_btn')
const notificationMenu = $('.notification_menu')
const notificationClose = $('#closeNotif')
const notificationList = $('.notifcation_list')

const conversationList = $('.conversation_list')
const chatEmpty = $('#chatEmpty')
const chatRoom = $('#chatRoom')
const chatAvatar = $('#chatAvatar')
const chatUserName = $('#chatUserName')
const chatUserStatus = $('#chatUserStatus')
const chatBody = $('#chatBody')
const messageInput = $('#messageInput')
const sendMessageBtn = $('#sendMessageBtn')

const chatApp = {

    avatarFile: null,
    hasNotification: false,
    currentConversation: null,
    conversations: [],
    config: JSON.parse(localStorage.getItem(LOGIN_STORAGE_KEY)) || {},

    setConfig: function (key, value) {
        this.config[key] = value

        localStorage.setItem(
            LOGIN_STORAGE_KEY,
            JSON.stringify(this.config)
        )
    },

    checkLogin: function () {
        if (!this.config.isLoggedIn || !this.config.user) {
            window.location.href = './login.html'
            return false
        }

        return true
    },

    loadUser: function () {
        if (this.config.isLoggedIn && this.config.user) {
            userName.textContent = this.config.user.username

            if (
                !this.config.user.avatar ||
                this.config.user.avatar === 'default_avt.png'
            ) {
                userAvt.src = './assests/img/default_avt.png'
            } else {
                userAvt.src =
                    `${API_URL}${this.config.user.avatar}`
            }
        }
    },

    openProfile: function () {
        profileName.value = this.config.user.username
        profileUserId.textContent = this.config.user.userid

        if (
            !this.config.user.avatar ||
            this.config.user.avatar === 'default_avt.png'
        ) {
            profileAvt.src = './assests/img/default_avt.png'
        } else {
            profileAvt.src =
                `${API_URL}${this.config.user.avatar}`
        }

        profileModal.classList.add('active')
    },

    closeProfile: function () {
        profileModal.classList.remove('active')
    },

    openLogout: function () {
        logoutModal.classList.add('active')
    },

    closeLogout: function () {
        logoutModal.classList.remove('active')
    },

    logout: function () {
        localStorage.removeItem(LOGIN_STORAGE_KEY)
        window.location.href = './login.html'
    },

    loadMessages: async function (conversationId) {
        try {
            const userId = this.config.user.id
            const response = await fetch(
                `${API_URL}/api/messages?conversation_id=${conversationId}&user_id=${userId}`
            )
            const result = await response.json()
            if (!result.success) {
                console.error(result.message)
                return
            }
            if (result.messages.length === 0) {
                chatBody.innerHTML = ''
                return
            }

            chatBody.innerHTML =
                result.messages.map((message, index) => {

                    const isMine =
                        String(message.sender_id) ===
                        String(userId)

                    const isLastMessage =
                        index === result.messages.length - 1

                    const showStatus =
                        isMine && isLastMessage

                    const previousMessage =
                        result.messages[index - 1]

                    const isSameSender =
                        previousMessage &&
                        String(previousMessage.sender_id) ===
                        String(message.sender_id)

                    const messageClass =
                        isMine
                            ? 'message sent'
                            : isSameSender
                                ? 'message received message_group'
                                : 'message received'

                    const avatar =
                        !message.sender_avatar ||
                            message.sender_avatar === 'default_avt.png'
                            ? './assests/img/default_avt.png'
                            : `${API_URL}${message.sender_avatar}`

                    // Trạng thái tin nhắn
                    const messageStatus =
                        message.status === 'seen'
                            ? 'Đã xem'
                            : message.status === 'delivered'
                                ? 'Đã nhận'
                                : 'Đã gửi'

                    return `
                    <div class="${messageClass}">

                        ${!isMine && !isSameSender
                            ? `
                                    <img
                                        class="message_avatar"
                                        src="${avatar}"
                                        alt=""
                                    >
                                `
                            : ''
                        }

                        <div class="message_content">

                            <p>
                                ${message.content}
                            </p>

                        </div>

                        ${showStatus
                            ? `
                                    <span class="message_status">
                                        ${messageStatus}
                                    </span>
                                `
                            : ''
                        }

                    </div>
                `
                }).join('')

            chatBody.scrollTop =
                chatBody.scrollHeight

        } catch (error) {

            console.error(
                'Lỗi loadMessages:',
                error
            )

        }
    },

    markMessagesSeen: async function (conversationId) {

        try {

            const response = await fetch(
                `${API_URL}/api/messages/seen`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        conversation_id: conversationId,
                        user_id: this.config.user.id
                    })
                }
            )

            const result = await response.json()

            if (!result.success) {
                console.error(result.message)
            }

        } catch (error) {

            console.error(
                'Lỗi markMessagesSeen:',
                error
            )

        }
    },



    openConversation: function (conversation) {

        this.currentConversation = conversation

        chatEmpty.style.display = 'none'
        chatRoom.style.display = 'flex'

        chatUserName.textContent =
            conversation.user.username

        if (
            !conversation.user.avatar ||
            conversation.user.avatar === 'default_avt.png'
        ) {
            chatAvatar.src =
                './assests/img/default_avt.png'
        } else {
            chatAvatar.src =
                `${API_URL}${conversation.user.avatar}`
        }

        chatUserStatus.textContent =
            'Đang hoạt động'

        this.markMessagesSeen(
            conversation.conversation_id
        )
        this.loadMessages(
            conversation.conversation_id
        )
    },

    updateNotificationBadge: function (hasNotification) {

        this.hasNotification = hasNotification

        if (hasNotification) {
            notificationIcon.classList.add(
                'has_notification'
            )
        } else {
            notificationIcon.classList.remove(
                'has_notification'
            )
        }
    },
    loadFriendRequests: async function () {

        try {

            const response = await fetch(
                `${API_URL}/api/friend-requests?userid=${this.config.user.userid}`
            )

            const result = await response.json()

            if (!result.success) {
                return
            }

            // Có lời mời kết bạn hay không
            this.updateNotificationBadge(
                result.requests.length > 0
            )

            // Hiển thị danh sách lời mời
            notificationList.innerHTML =
                result.requests.map(request => {

                    const avatar =
                        !request.avatar ||
                            request.avatar === 'default_avt.png'
                            ? './assests/img/default_avt.png'
                            : `${API_URL}${request.avatar}`

                    return `
                    <div
                        class="notif_item"
                        data-request-id="${request.id}"
                    >

                        <img
                            src="${avatar}"
                            alt=""
                        >

                        <h4 class="username">
                            ${request.username}
                        </h4>

                        <div class="notif_act">

                            <button
                                type="button"
                                class="btn btn-agree btn-notif"
                                data-action="accept"
                                data-request-id="${request.id}"
                            >
                                Đồng ý
                            </button>

                            <button
                                type="button"
                                class="btn btn-notif"
                                data-action="reject"
                                data-request-id="${request.id}"
                            >
                                Từ chối
                            </button>

                        </div>

                    </div>
                `
                }).join('')

        } catch (error) {

            console.error(error)

        }
    },
    loadConversations: async function () {
        try {
            const userId = this.config.user.id
            const response = await fetch(
                `${API_URL}/api/conversations?user_id=${userId}`
            )
            const result = await response.json()

            console.log('conversations:', result)

            // const result = await response.json()
            // if (!result.success) {
            //     return
            // }
            this.conversations = result.conversations
            if (result.conversations.length === 0) {

                conversationList.innerHTML = ''

                return
            }
            conversationList.innerHTML =
                result.conversations.map(conversation => {
                    const user = conversation.user
                    const avatar =
                        !user.avatar ||
                            user.avatar === 'default_avt.png'
                            ? './assests/img/default_avt.png'
                            : `${API_URL}${user.avatar}`

                    let messagePreview = 'Chưa có tin nhắn'

                    if (conversation.last_message) {

                        const isMine =
                            String(conversation.last_message.sender_id) ===
                            String(this.config.user.id)

                        messagePreview =
                            isMine
                                ? `Bạn: ${conversation.last_message.content}`
                                : conversation.last_message.content
                    }
                    return `
                    <div
                        class="conversation_item"
                        data-conversation-id="${conversation.conversation_id}"
                    >
                        <div class="conversation_avatar">
                            <img
                                src="${avatar}"
                                alt=""
                            >
                            <span class="online"></span>
                        </div>
                        <div class="conversation_content">
                            <div class="conversation_top">
                                <h3>
                                    ${user.username}
                                </h3>
                                <span class="conversation_time">
                                </span>
                            </div>
                            <div class="conversation_bottom">
                                <p class="conversation_message">
                                    ${messagePreview}
                                </p>
                            </div>
                        </div>
                    </div>
                `
                }).join('')



        } catch (error) {

            console.error(error)

        }
    },

    handleEvent: function () {
        // ==================== TURN ON/OFF NOTIFICATION =======
        notificationIcon.onclick = (e) => {
            e.stopPropagation();
            notificationMenu.classList.add('open')
            this.loadFriendRequests()
        }

        notificationClose.onclick = (e) => {
            e.stopPropagation();
            notificationMenu.classList.remove('open')
        }

        notificationList.onclick = async (e) => {

            const button =
                e.target.closest('.btn-notif')

            if (!button) {
                return
            }

            const action =
                button.dataset.action

            const requestId =
                button.dataset.requestId

            if (action !== 'accept') {
                return
            }

            try {

                const response = await fetch(
                    `${API_URL}/api/accept-friend-request`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            request_id: requestId
                        })
                    }
                )

                const result =
                    await response.json()

                if (!result.success) {
                    alert(result.message)
                    return
                }

                // Cập nhật lại danh sách thông báo
                this.loadFriendRequests()

                // Hiện người bạn vừa kết bạn trong Conversation
                this.loadConversations()

            } catch (error) {

                console.error(error)

                alert(
                    'Không thể kết nối đến máy chủ'
                )
            }
        }

        // ==================== PROFILE ====================

        profileBtn.onclick = () => {
            this.openProfile()
        }

        closeProfile.onclick = () => {
            this.closeProfile()
        }

        cancelProfile.onclick = () => {
            this.closeProfile()
        }

        profileModal.onmousedown = (e) => {

            if (e.target !== profileModal) {
                return
            }

            profileModal.classList.remove('active')
        }

        copyUserId.onclick = async () => {

            try {

                await navigator.clipboard.writeText(
                    this.config.user.userid
                )

                copyUserId.innerHTML =
                    '<i class="fa-solid fa-check"></i>'

                setTimeout(() => {
                    copyUserId.innerHTML =
                        '<i class="fa-regular fa-copy"></i>'
                }, 1500)

            } catch (error) {

                console.error(error)

                alert('Không thể sao chép ID')
            }
        }

        // ==================== PASSWORD ====================

        const passwordError = $('#passwordError')

        const resetPassword = () => {
            passwordInputs.forEach((input) => {
                input.value = ''
            })

            hideError(passwordError)

            passwordModal.classList.remove('active')
        }

        userPassword.onclick = () => {
            passwordModal.classList.add('active')
        }

        closePassword.onclick = resetPassword
        cancelPassword.onclick = resetPassword

        passwordModal.onclick = (e) => {
            if (e.target === passwordModal) {
                resetPassword()
            }
        }

        clearErrorOnInput(
            passwordInputs,
            passwordError
        )

        savePassword.onclick = async () => {

            if (
                !validateChangePassword(
                    currentPassword,
                    newPassword,
                    confirmPassword,
                    passwordError
                )
            ) {
                return
            }

            try {

                const response = await fetch(
                    `${API_URL}/api/change-password`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            userid: this.config.user.userid,
                            current_password:
                                currentPassword.value.trim(),
                            new_password:
                                newPassword.value.trim()
                        })
                    }
                )

                const result = await response.json()

                if (!result.success) {
                    showError(
                        passwordError,
                        result.message
                    )
                    return
                }

                alert('Đổi mật khẩu thành công')

                resetPassword()

            } catch (error) {

                console.error(error)

                showError(
                    passwordError,
                    'Không thể kết nối đến máy chủ'
                )
            }
        }

        // ==================== LOGOUT ====================

        logoutBtn.onclick = () => {
            this.openLogout()
        }

        closeLogout.onclick = () => {
            this.closeLogout()
        }

        cancelLogout.onclick = () => {
            this.closeLogout()
        }

        agreeLogout.onclick = () => {
            this.logout()
        }

        logoutModal.onclick = (e) => {
            if (e.target === logoutModal) {
                this.closeLogout()
            }
        }

        // ==================== AVATAR ====================

        avatarInput.onchange = async (e) => {

            const file = e.target.files[0]

            if (!file) {
                return
            }

            try {

                const processedFile =
                    await avatarTool.process(file)

                this.avatarFile = processedFile

                profileAvt.src =
                    URL.createObjectURL(processedFile)

            } catch (error) {

                console.error(error)
                alert('Không thể xử lý ảnh')

            }
        }

        // ==================== SAVE PROFILE ====================

        saveProfile.onclick = async () => {
            const newUsername = profileName.value.trim()
            const oldUsername = this.config.user.username
            const avatarFile = this.avatarFile

            if (newUsername === '') {
                alert('Tên người dùng không được để trống')
                return
            }

            const usernameChanged = newUsername !== oldUsername
            const avatarChanged = !!avatarFile

            if (!usernameChanged && !avatarChanged) {
                profileModal.classList.remove('active')
                return
            }

            try {
                // Cập nhật username
                if (usernameChanged) {
                    const response = await fetch(
                        `${API_URL}/api/update-profile`,
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                userid: this.config.user.userid,
                                username: newUsername
                            })
                        }
                    )

                    const result = await response.json()

                    if (!result.success) {
                        alert(result.message)
                        return
                    }

                    this.config.user.username = result.username
                    userName.textContent = result.username
                }

                // Cập nhật avatar
                if (avatarChanged) {
                    const formData = new FormData()

                    formData.append(
                        'userid',
                        this.config.user.userid
                    )

                    formData.append(
                        'avatar',
                        avatarFile
                    )

                    const response = await fetch(
                        `${API_URL}/api/update-avatar`,
                        {
                            method: 'POST',
                            body: formData
                        }
                    )

                    const result = await response.json()

                    if (!result.success) {
                        alert(result.message)
                        return
                    }

                    this.config.user.avatar = result.avatar

                    userAvt.src =
                        `${API_URL}${result.avatar}?t=${Date.now()}`

                    profileAvt.src =
                        `${API_URL}${result.avatar}?t=${Date.now()}`
                    this.avatarFile = null
                }

                this.setConfig(
                    'user',
                    this.config.user
                )

                profileModal.classList.remove('active')

                alert('Cập nhật thông tin thành công')

            } catch (error) {
                console.error(error)
                alert('Không thể kết nối đến máy chủ')
            }
        }

        // ==================== ADD FRIEND MODAL ================

        closeAddFriend.onclick = () => {
            addfrModal.classList.remove('active')
        }

        // addFriendBtn.onclick = () => {
        //     addfrModal.classList.add('active')
        // }

        addFriendBtns.forEach((addFriendBtn, index) => {
            addFriendBtn.onclick = () => {
                addfrModal.classList.add('active')
            }
        })

        addfrModal.onclick = (e) => {
            if (e.target === addfrModal) {
                addfrModal.classList.remove('active')
            }
        }
        friendUserSearch.oninput = async () => {

            const keyword =
                friendUserSearch.value.trim()
            if (keyword === '') {
                friendSearchResult.innerHTML = ''
                return
            }
            try {
                const response = await fetch(
                    `${API_URL}/api/search-user?keyword=${encodeURIComponent(keyword)}&userid=${this.config.user.userid}`
                )
                const result = await response.json()
                if (!result.success) {
                    friendSearchResult.innerHTML = ''
                    return
                }
                if (result.users.length === 0) {
                    friendSearchResult.innerHTML = `
                    <div class="modal_empty">
                        <i class="fa-solid fa-user-xmark"></i>
                        <p>Không tìm thấy người dùng</p>
                    </div>`
                    return
                }

                friendSearchResult.innerHTML = result.users.map(user => {

                    const avatar =
                        !user.avatar || user.avatar === 'default_avt.png'
                            ? './assests/img/default_avt.png'
                            : `${API_URL}${user.avatar}`
                    let friendButton = ''
                    if (user.friend_status === 'accepted') {

                        friendButton = `
                                            <button
                                                type="button"
                                                class="btn btn_addfriend"
                                                disabled>
                                                Đã kết bạn
                                            </button>
                                        `

                    } else if (user.friend_status === 'sent') {

                        friendButton = `
                                            <button
                                                type="button"
                                                class="btn btn_addfriend"
                                                disabled>
                                                Đã gửi
                                            </button>
                                        `

                    } else if (user.friend_status === 'received') {

                        friendButton = `
                                            <button
                                                type="button"
                                                class="btn btn_addfriend"
                                                disabled>
                                                Chờ bạn xác nhận
                                            </button>
                                        `

                    } else {

                        friendButton = `
                                            <button
                                                type="button"
                                                class="btn btn_addfriend"
                                                data-userid="${user.userid}">
                                                Kết bạn
                                            </button>
                                        `
                    }

                    return `
                                <div class="modal_item">
                                    <img src="${avatar}" alt="">

                                    <div class="modal_container">
                                        <h4 class="modal_name">
                                            ${user.username}
                                        </h4>

                                        <p class="modal_id">
                                            ${user.userid}
                                        </p>
                                    </div>

                                    ${friendButton}
                                </div>
                            `
                }).join('')
                const addButtons =
                    friendSearchResult.querySelectorAll(
                        '.btn_addfriend'
                    )

                addButtons.forEach((button) => {

                    button.onclick = async () => {

                        const receiverUserid =
                            button.dataset.userid

                        try {

                            const response = await fetch(
                                `${API_URL}/api/send-friend-request`,
                                {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({
                                        sender_userid:
                                            this.config.user.userid,

                                        receiver_userid:
                                            receiverUserid
                                    })
                                }
                            )

                            const result =
                                await response.json()

                            if (!result.success) {
                                alert(result.message)
                                return
                            }

                            button.textContent = 'Đã gửi'
                            button.disabled = true

                        } catch (error) {

                            console.error(error)

                            alert(
                                'Không thể kết nối đến máy chủ'
                            )
                        }
                    }
                })
            } catch (error) {
                console.error(error)
                friendSearchResult.innerHTML = `
                <div class="modal_empty">
                    <p>Không thể kết nối đến máy chủ</p>
                </div>`
            }
        }

        // CONVERSATION
        conversationList.onclick = (e) => {

            const conversationItem =
                e.target.closest('.conversation_item')

            if (!conversationItem) {
                return
            }

            const conversationId =
                conversationItem.dataset.conversationId

            const conversation =
                this.conversations.find(
                    conversation =>
                        String(conversation.conversation_id) ===
                        String(conversationId)
                )

            if (!conversation) {
                return
            }

            document
                .querySelectorAll('.conversation_item')
                .forEach(item => {
                    item.classList.remove('active')
                })

            conversationItem.classList.add('active')

            this.openConversation(conversation)
        }

        // ==================== SEND MESSAGE ====================

        sendMessageBtn.onclick = async () => {

            const content =
                messageInput.value.trim()

            if (content === '') {
                return
            }

            if (!this.currentConversation) {
                return
            }

            try {

                const response = await fetch(
                    `${API_URL}/api/messages`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            conversation_id:
                                this.currentConversation.conversation_id,

                            sender_id:
                                this.config.user.id,

                            content: content
                        })
                    }
                )

                const result =
                    await response.json()

                if (!result.success) {

                    alert(result.message)

                    return
                }

                messageInput.value = ''

                this.loadMessages(
                    this.currentConversation.conversation_id
                )

            } catch (error) {

                console.error(error)

                alert(
                    'Không thể kết nối đến máy chủ'
                )
            }
        }

        messageInput.onkeydown = (e) => {

            if (e.key !== 'Enter') {
                return
            }

            e.preventDefault()

            sendMessageBtn.click()
        }
    },

    start: function () {
        const socket = io(SOCKET_URL)

        socket.on('connect', () => {
            console.log('Đã kết nối Socket.IO:', socket.id)
        })

        socket.on('disconnect', () => {
            console.log('Đã ngắt kết nối Socket.IO')
        })


        if (!this.checkLogin()) {
            return
        }

        this.loadUser()
        this.handleEvent()
        // Kiểm tra lời mời ngay khi mở trang
        this.loadFriendRequests()
        this.loadConversations()
        setInterval(() => {

            this.loadFriendRequests()

        }, 5000)
    }
}

chatApp.start()