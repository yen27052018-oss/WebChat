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

const imageBtn = $('#imageBtn')
const imageInput = $('#imageInput')
const fileBtn = $('#fileBtn')
const fileInput = $('#fileInput')
const voiceBtn = $('#voiceBtn')
const callBtn = $('#btnCall')
const callVideoBtn = $('#btnCallVideo')

const callOverlay = $('.call_overlay')
const callClose = $('.call_close')
const callReject = $('.call_reject')
const callWindow = $('.call_window')
const callAccept = $('.call_accept')
const callUserName = $('.call_window_name')
const callAvatar = $('.call_window_avatar img')
const callTitle = $('.call_title')
const callBackground = $('.call_background img')

const callMinimize = $('.call_minimize')
const callMic = $('.call_mic')
const callVideo = $('.call_video')
const callEnd = $('.call_end')

const chatApp = {
    isCallPopupOpen: false,
    isTyping: false,
    typingTimeout: null,
    avatarFile: null,
    hasNotification: false,
    mediaRecorder: null,
    currentConversation: null,
    isMicOn: true,
    isVideoOn: false,

    // CALL
    callState: 'idle',
    callUserId: null,
    callTimer: null,
    callStartTime: null,

    // WEBRTC
    peerConnection: null, // thiết lập và quản lý kết nối
    localStream: null, // đường truyền thiết bị gần
    remoteStream: null, // đường truyền thiết bị xa
    remoteAudio: null,
    pendingIceCandidates: [],

    socket: null,
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

    getCallUser: function (userId) {

        return this.conversations.find(
            conversation =>
                String(conversation.user.id) ===
                String(userId)
        )?.user || null
    },

    setCallUserInfo: function (userId) {

        const user = this.getCallUser(userId)

        if (!user) {
            return
        }

        callTitle.textContent =
            user.username

        callUserName.textContent =
            user.username

        let avatarSrc =
            './assests/img/default_avt.png'

        if (
            user.avatar &&
            user.avatar !== 'default_avt.png'
        ) {
            avatarSrc =
                `${API_URL}${user.avatar}`
        }

        callAvatar.src =
            avatarSrc

        callBackground.src =
            avatarSrc
    },

    // Web rtc 

    formatCallDuration: function (seconds) {

        seconds = Number(seconds) || 0

        const hours =
            Math.floor(seconds / 3600)

        const minutes =
            Math.floor(
                (seconds % 3600) / 60
            )

        const secs =
            seconds % 60

        if (hours > 0) {

            return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`

        }

        return `${minutes}:${String(secs).padStart(2, '0')}`
    },

    createPeerConnection: function () {

        const configuration = {
            iceServers: [
                {
                    urls: 'stun:stun.l.google.com:19302'
                }
            ]
        }

        this.peerConnection =
            new RTCPeerConnection(
                configuration
            )

        this.remoteStream = new MediaStream()

        this.remoteAudio = new Audio()

        this.remoteAudio.autoplay = true

        this.remoteAudio.srcObject = this.remoteStream

        console.log(
            'Đã tạo RTCPeerConnection'
        )

        this.peerConnection.onicecandidate =
            (event) => {

                if (!event.candidate) {
                    return
                }

                this.socket.emit(
                    'webrtc_ice_candidate',
                    {
                        user_id:
                            this.config.user.id,

                        target_user_id:
                            this.callUserId,

                        candidate:
                            event.candidate
                    }
                )
            }

        this.peerConnection.ontrack =
            (event) => {

                console.log(
                    'Đã nhận audio từ người bên kia'
                )

                this.remoteStream.addTrack(
                    event.track
                )

                this.remoteAudio
                    .play()
                    .catch(error => {
                        if(error.name !== 'AbortError')
                        console.error(
                            'Không thể phát audio:',
                            error
                        )
                    })
            }

        this.peerConnection.onconnectionstatechange =
            () => {

                const state =
                    this.peerConnection.connectionState

                console.log(
                    'WebRTC connection state:',
                    state
                )

                if (state === 'connected') {

                    $('.call_window_status')
                        .textContent =
                        'Đã kết nối'

                    console.log(
                        'WebRTC đã kết nối thành công'
                    )
                }

                if (state === 'failed') {

                    $('.call_window_status')
                        .textContent =
                        'Kết nối thất bại'

                    console.error(
                        'WebRTC connection failed'
                    )
                }
            }
    },

    getLocalStream: async function () {

        try {

            const stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                })

            this.localStream = stream

            console.log(
                'Đã lấy được microphone'
            )

            return stream

        } catch (error) {

            if (error.name === 'NotFoundError') {

                alert(
                    'Không tìm thấy microphone. Vui lòng kiểm tra microphone hoặc kết nối tai nghe có mic.'
                )

            } else if (error.name === 'NotAllowedError') {

                alert(
                    'Bạn chưa cho phép trình duyệt sử dụng microphone.'
                )

            } else {

                alert(
                    'Không thể truy cập microphone.'
                )
            }

            return null
        }
    },

    addLocalTracks: function () {

        if (
            !this.peerConnection ||
            !this.localStream
        ) {
            return
        }

        this.localStream
            .getTracks()
            .forEach(track => {

                this.peerConnection.addTrack(
                    track,
                    this.localStream
                )

            })

        console.log(
            'Đã thêm microphone vào WebRTC'
        )
    },

    createOffer: async function () {

        if (!this.peerConnection) {
            return
        }

        try {

            const offer =
                await this.peerConnection
                    .createOffer()

            await this.peerConnection
                .setLocalDescription(offer)

            console.log(
                'Đã tạo WebRTC offer'
            )

            this.socket.emit(
                'webrtc_offer',
                {
                    user_id:
                        this.config.user.id,

                    target_user_id:
                        this.callUserId,

                    offer: offer
                }
            )

        } catch (error) {

            console.error(
                'Không thể tạo WebRTC offer:',
                error
            )
        }
    },

    createAnswer: async function () {

        if (!this.peerConnection) {
            return
        }

        try {

            const answer =
                await this.peerConnection
                    .createAnswer()

            await this.peerConnection
                .setLocalDescription(answer)

            console.log(
                'Đã tạo WebRTC answer'
            )

            this.socket.emit(
                'webrtc_answer',
                {
                    user_id:
                        this.config.user.id,

                    target_user_id:
                        this.callUserId,

                    answer: answer
                }
            )

        } catch (error) {

            console.error(
                'Không thể tạo WebRTC answer:',
                error
            )
        }
    },

    handleIceCandidate: async function (candidate) {

        if (!this.peerConnection) {
            return
        }

        if (
            !this.peerConnection.remoteDescription
        ) {
            this.pendingIceCandidates.push(
                candidate
            )

            console.log(
                'ICE candidate được lưu tạm'
            )

            return
        }

        try {

            await this.peerConnection
                .addIceCandidate(
                    new RTCIceCandidate(candidate)
                )

            console.log(
                'Đã thêm ICE candidate'
            )

        } catch (error) {

            console.error(
                'Không thể thêm ICE candidate:',
                error
            )
        }
    },

    cleanupWebRTC: function () {

        console.log(
            'Đang dọn WebRTC...'
        )

        // Dừng microphone
        if (this.localStream) {

            this.localStream
                .getTracks()
                .forEach(track => {
                    track.stop()
                })

            this.localStream = null
        }

        // Dừng remote audio
        if (this.remoteAudio) {

            this.remoteAudio.pause()

            this.remoteAudio.srcObject = null

            this.remoteAudio = null
        }

        // Xóa remote stream
        this.remoteStream = null

        // Đóng PeerConnection
        if (this.peerConnection) {

            this.peerConnection.close()

            this.peerConnection = null
        }

        // Xóa ICE candidate cũ
        this.pendingIceCandidates = []

        console.log(
            'Đã dọn WebRTC'
        )
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

    getCallMessage: function (message) {

        const isMine =
            String(message.sender_id) ===
            String(this.config.user.id)

        const callType =
            'Cuộc gọi thoại'

        switch (message.content) {

            case 'accepted':

                return {
                    title: isMine
                        ? 'Cuộc gọi đi'
                        : 'Cuộc gọi đến',

                    subText: callType,

                    className: ''
                }

            case 'rejected':

                return {
                    title: isMine
                        ? 'Người dùng từ chối'
                        : 'Bạn đã từ chối',

                    subText: callType,

                    className: 'call_failed'
                }

            case 'cancelled':

                return {
                    title: isMine
                        ? 'Bạn đã hủy'
                        : 'Bạn bị nhỡ',

                    subText: callType,

                    className: 'call_failed'
                }

            case 'timeout':

                return {
                    title: isMine
                        ? 'Cuộc gọi đi'
                        : 'Bạn bị nhỡ',

                    subText: callType,

                    className: isMine
                        ? ''
                        : 'call_failed'
                }

            case 'ended':

                return {
                    title: isMine
                        ? 'Bạn đã hủy'
                        : 'Bạn bị nhỡ',

                    subText: callType,

                    className: 'call_failed'
                }

            default:

                return {
                    title: isMine
                        ? 'Cuộc gọi đi'
                        : 'Cuộc gọi đến',

                    subText: callType,

                    className: ''
                }
        }
    },

    getCallPreview: function (message) {

        const isMine =
            String(message.sender_id) ===
            String(this.config.user.id)

        return isMine
            ? 'Bạn: 📞 Cuộc gọi đi'
            : '📞 Cuộc gọi đến'
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

                            ${message.message_type === 'image'
                            ? `
                                <img
                                    class="message_image"
                                    src="${message.content}"
                                    alt="Ảnh đã gửi"
                                >`
                            : message.message_type === 'file'
                                ? `<a
                                        class="message_file"
                                        href="${message.content}"
                                        target="_blank"
                                        download="${message.file_name}"
                                    >
                                        <i class="fa-regular fa-file"></i>

                                        <span>
                                            ${message.file_name}
                                        </span>
                                    </a>`
                                : message.message_type === 'voice'
                                    ? `
                                        <div class="message_voice">
                                            <button class="voice_play">
                                                <i class="fa-solid fa-play"></i>
                                            </button>

                                            <input
                                                type="range"
                                                class="voice_progress"
                                                min="0"
                                                max="100"
                                                value="0"
                                                step="0.01"
                                            >

                                            <span class="voice_time">
                                                0:00
                                            </span>

                                            <audio
                                                class="voice_audio"
                                                src="${message.content}"
                                            ></audio>
                                        </div>
                                    `
                                    : message.message_type === 'call'
                                        ? (() => {

                                            const callMessage =
                                                this.getCallMessage(message)

                                            return `
                                                        <div class="message_call">

                                                            <span class="message_call_title ${callMessage.className}">
                                                                ${callMessage.title}
                                                            </span>

                                                            <div class="message_call_bottom">

                                                                <i class="fa-solid fa-phone"></i>

                                                                ${message.content === 'accepted'
                                                    ? `
                                                                            <span class="message_call_duration">
                                                                                ${this.formatCallDuration(
                                                        message.call_duration
                                                    )}
                                                                            </span>
                                                                        `
                                                    : `
                                                                            <span class="message_call_type">
                                                                                ${callMessage.subText}
                                                                            </span>
                                                                        `
                                                }

                                                            </div>

                                                        </div>
                                                    `
                                        })()
                                        : `
                                            <p>
                                                ${message.content}
                                            </p>`

                        }
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

            const messageImages =
                chatBody.querySelectorAll('.message_image')

            if (messageImages.length > 0) {

                await Promise.all(
                    [...messageImages].map(image => {

                        if (image.complete) {
                            return Promise.resolve()
                        }

                        return new Promise(resolve => {

                            image.onload = resolve
                            image.onerror = resolve

                        })

                    })
                )
            }

            const lastMessage =
                chatBody.lastElementChild

            if (lastMessage) {

                lastMessage.scrollIntoView({
                    behavior: 'smooth',
                    block: 'end'
                })

            }
            this.handleVoiceEvents()

        } catch (error) {

            console.error(
                'Lỗi loadMessages:',
                error
            )

        }
    },

    markMessagesSeen: function (conversationId) {

        if (!this.socket) {
            return
        }
        this.socket.emit('message_seen', {
            conversation_id: conversationId,
            user_id: this.config.user.id
        })
    },

    appendMessage: function (message) {

        const oldStatus =
            chatBody.querySelectorAll('.message_status')

        oldStatus.forEach(status => {
            status.remove()
        })

        const messageElement =
            document.createElement('div')

        const isMine =
            String(message.sender_id) ===
            String(this.config.user.id)

        const messageStatus =
            message.status === 'seen'
                ? 'Đã xem'
                : message.status === 'delivered'
                    ? 'Đã nhận'
                    : 'Đã gửi'

        messageElement.className =
            isMine
                ? 'message sent'
                : 'message received'

        messageElement.innerHTML = `
            <div class="message_content">

                ${message.message_type === 'image'
                ? `
                    <img
                        class="message_image"
                        src="${message.content}"
                        alt="Ảnh đã gửi"
                    >
                    `
                : message.message_type === 'file'
                    ? `
                        <a
                            class="message_file"
                            href="${message.content}"
                            target="_blank"
                            download="${message.file_name}"
                        >
                            <i class="fa-regular fa-file"></i>

                            <span>
                                ${message.file_name}
                            </span>
                        </a>
                    `
                    : message.message_type === 'voice'
                        ? `
                            <div class="message_voice">
                                <button class="voice_play">
                                    <i class="fa-solid fa-play"></i>
                                </button>

                                <input
                                    type="range"
                                    class="voice_progress"
                                    min="0"
                                    max="100"
                                    value="0"
                                    step="0.01"
                                >

                                <span class="voice_time">
                                    0:00
                                </span>

                                <audio
                                    class="voice_audio"
                                    src="${message.content}"
                                ></audio>
                            </div>
                        `
                        : message.message_type === 'call' ? (() => {
                            const callMessage =
                                this.getCallMessage(message)

                            return `
                                <div class="message_call">
                                    <span class="message_call_title ${callMessage.className}">
                                        ${callMessage.title}
                                    </span>
                                    <div class="message_call_bottom">
                                        <i class="fa-solid fa-phone"></i>
                                        ${message.content === 'accepted' ? `
                                                <span class="message_call_duration">
                                                    ${this.formatCallDuration(
                                message.call_duration
                            )}
                                                </span>
                                            `: `
                                                <span class="message_call_type">
                                                    ${callMessage.subText}
                                                </span>
                                            `
                                }
                                    </div>
                                </div>

                            `
                        })() : `<p>${message.content}</p>`
            }

            </div>

            ${isMine
                ? `
                    <span class="message_status">
                        ${messageStatus}
                    </span>
                    `
                : ''
            }
        `

        chatBody.appendChild(messageElement)

        messageElement.scrollIntoView({
            behavior: 'smooth',
            block: 'end'
        })

        this.handleVoiceEvents()
    },

    handleVoiceEvents: function () {

        const voiceList =
            document.querySelectorAll('.message_voice')


        voiceList.forEach(voice => {

            const playBtn =
                voice.querySelector('.voice_play')

            const audio =
                voice.querySelector('.voice_audio')

            const progress =
                voice.querySelector('.voice_progress')

            const time =
                voice.querySelector('.voice_time')


            // Khi audio load xong
            audio.onloadedmetadata = () => {

                progress.max =
                    audio.duration

                progress.value =
                    0


                const minutes =
                    Math.floor(audio.duration / 60)

                const seconds =
                    Math.floor(audio.duration % 60)
                        .toString()
                        .padStart(2, '0')

                time.textContent =
                    `${minutes}:${seconds}`
            }


            // Play / Pause
            playBtn.onclick = () => {

                if (audio.paused) {

                    // Dừng những voice khác
                    voiceList.forEach(otherVoice => {

                        const otherAudio =
                            otherVoice.querySelector(
                                '.voice_audio'
                            )

                        const otherPlayBtn =
                            otherVoice.querySelector(
                                '.voice_play'
                            )

                        if (
                            otherAudio !== audio &&
                            !otherAudio.paused
                        ) {

                            otherAudio.pause()

                            otherPlayBtn.innerHTML =
                                '<i class="fa-solid fa-play"></i>'
                        }
                    })


                    audio.play()

                    playBtn.innerHTML =
                        '<i class="fa-solid fa-pause"></i>'

                } else {

                    audio.pause()

                    playBtn.innerHTML =
                        '<i class="fa-solid fa-play"></i>'
                }
            }


            // Audio đang chạy
            audio.ontimeupdate = () => {

                if (!audio.duration) {
                    return
                }


                // Đồng bộ thanh range
                progress.value =
                    audio.currentTime


                // Đồng bộ thời gian
                const minutes =
                    Math.floor(audio.currentTime / 60)

                const seconds =
                    Math.floor(audio.currentTime % 60)
                        .toString()
                        .padStart(2, '0')

                time.textContent =
                    `${minutes}:${seconds}`
            }


            // Kéo / click input range
            progress.oninput = () => {

                audio.currentTime =
                    Number(progress.value)


                const minutes =
                    Math.floor(audio.currentTime / 60)

                const seconds =
                    Math.floor(audio.currentTime % 60)
                        .toString()
                        .padStart(2, '0')

                time.textContent =
                    `${minutes}:${seconds}`
            }


            // Phát xong
            audio.onended = () => {

                playBtn.innerHTML =
                    '<i class="fa-solid fa-play"></i>'


                progress.value =
                    0


                const minutes =
                    Math.floor(audio.duration / 60)

                const seconds =
                    Math.floor(audio.duration % 60)
                        .toString()
                        .padStart(2, '0')

                time.textContent =
                    `${minutes}:${seconds}`
            }

        })
    },

    joinConversation: function (conversationId) {

        if (!this.socket) {
            return
        }

        this.socket.emit('join_conversation', {

            conversation_id: conversationId,

            user_id: this.config.user.id

        })

    },

    checkUserOnline: function (userId) {

        if (!this.socket) {
            return
        }

        this.socket.emit('check_user_online', {
            user_id: userId
        })
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
            'Đang kiểm tra...'

        this.joinConversation(
            conversation.conversation_id
        )

        this.checkUserOnline(
            conversation.user.id
        )

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

                        const messageType =
                            conversation.last_message.message_type

                        if (messageType === 'image') {
                            messagePreview =
                                isMine
                                    ? 'Bạn: Hình ảnh'
                                    : 'Hình ảnh'

                        } else if (messageType === 'file') {

                            messagePreview =
                                isMine
                                    ? `Bạn: 📎 ${conversation.last_message.file_name}`
                                    : `📎 ${conversation.last_message.file_name}`

                        } else if (messageType === 'voice') {

                            messagePreview =
                                isMine
                                    ? 'Bạn: 🎤 Tin nhắn thoại'
                                    : '🎤 Tin nhắn thoại'

                        } else if (messageType === 'call') {

                            messagePreview =
                                this.getCallPreview(
                                    conversation.last_message
                                )
                        }
                        else {
                            messagePreview =
                                isMine
                                    ? `Bạn: ${conversation.last_message.content}`
                                    : conversation.last_message.content
                        }
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
                        </div>
                        <div class="conversation_content">
                            <div class="conversation_top">
                                <h3 class="conversation_name">
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

    updateConversationPreview: function (message) {

        const conversationItem =
            conversationList.querySelector(
                `[data-conversation-id="${message.conversation_id}"]`
            )

        if (!conversationItem) {
            return
        }

        const messagePreview =
            conversationItem.querySelector(
                '.conversation_message'
            )

        if (!messagePreview) {
            return
        }

        const isMine =
            String(message.sender_id) ===
            String(this.config.user.id)

        if (message.message_type === 'image') {

            messagePreview.textContent =
                isMine
                    ? 'Bạn: Hình ảnh'
                    : 'Hình ảnh'

        } else if (message.message_type === 'file') {

            messagePreview.textContent =
                isMine
                    ? `Bạn: 📎 ${message.file_name}`
                    : `📎 ${message.file_name}`

        } else if (message.message_type === 'voice') {

            messagePreview.textContent =
                isMine
                    ? 'Bạn: 🎤 Tin nhắn thoại'
                    : '🎤 Tin nhắn thoại'

        } else if (message.message_type === 'call') {

            messagePreview.textContent =
                this.getCallPreview(message)

        } else {

            messagePreview.textContent =
                isMine
                    ? `Bạn: ${message.content}`
                    : message.content
        }

        conversationList.prepend(
            conversationItem
        )
    },

    compressImage: function (image) {

        return new Promise((resolve, reject) => {

            const reader = new FileReader()

            reader.onload = function (event) {

                const img = new Image()

                img.onload = function () {

                    const maxWidth = 1280
                    const maxHeight = 1280

                    let width = img.width
                    let height = img.height

                    if (
                        width > maxWidth ||
                        height > maxHeight
                    ) {

                        const ratio = Math.min(
                            maxWidth / width,
                            maxHeight / height
                        )

                        width = Math.round(width * ratio)
                        height = Math.round(height * ratio)
                    }

                    const canvas = document.createElement('canvas')

                    canvas.width = width
                    canvas.height = height

                    const context = canvas.getContext('2d')

                    context.drawImage(
                        img,
                        0,
                        0,
                        width,
                        height
                    )

                    canvas.toBlob(
                        function (blob) {

                            if (!blob) {
                                reject(
                                    new Error(
                                        'Không thể nén ảnh'
                                    )
                                )
                                return
                            }

                            const compressedImage =
                                new File(
                                    [blob],
                                    image.name,
                                    {
                                        type: 'image/jpeg',
                                        lastModified: Date.now()
                                    }
                                )

                            resolve(compressedImage)

                        },
                        'image/jpeg',
                        0.8
                    )
                }

                img.onerror = function () {
                    reject(
                        new Error(
                            'Không thể đọc ảnh'
                        )
                    )
                }

                img.src = event.target.result
            }

            reader.onerror = function () {
                reject(
                    new Error(
                        'Không thể đọc file'
                    )
                )
            }

            reader.readAsDataURL(image)
        })
    },

    openCallPopup: function () {
        callOverlay.style.display = 'flex'
        this.isCallPopupOpen = true
    },

    closeCallPopup: function () {
        callOverlay.style.display = 'none'
        this.isCallPopupOpen = false
    },

    endCall: function () {
        if (this.callUserId) {
            this.socket.emit(
                'call_end',
                {
                    user_id: this.config.user.id
                }
            )
        }
        this.stopCallTimer()
        this.callState = 'idle'
        this.callUserId = null
        this.isMicOn = true
        this.isVideoOn = false

        callOverlay.style.display = 'none'
        callWindow.style.display = 'none'

        callMic.innerHTML =
            '<i class="fa-solid fa-microphone"></i>'

        callMic.classList.remove('off')

        callVideo.innerHTML =
            '<i class="fa-solid fa-video-slash"></i>'

        callVideo.classList.remove('off')

        callWindow.classList.remove('minimized')


        callAccept.style.display = 'flex'
        callReject.style.display = 'flex'

        callReject.innerHTML = `
        <i class="fa-solid fa-phone-slash"></i>
        <span>Từ chối</span>
    `
    },

    startCallTimer: function () {

        this.callStartTime =
            Date.now()

        this.callTimer =
            setInterval(() => {

                const elapsed =
                    Math.floor(
                        (Date.now() - this.callStartTime) / 1000
                    )

                const minutes =
                    Math.floor(elapsed / 60)

                const seconds =
                    (elapsed % 60)
                        .toString()
                        .padStart(2, '0')

                const duration =
                    $('.call_duration')

                if (duration) {

                    duration.textContent =
                        `${minutes}:${seconds}`
                }

            }, 1000)
    },

    stopCallTimer: function () {

        clearInterval(
            this.callTimer
        )

        this.callTimer = null

        this.callStartTime = null
    },

    callUser: function (userId) {

        if (this.callState !== 'idle') {
            return
        }

        this.callState = 'calling'
        this.callUserId = userId
        this.setCallUserInfo(userId)
        this.openCallPopup()

        // Thông tin popup
        $('.call_status').textContent = 'Đang gọi...'

        // Người gọi không cần nút chấp nhận
        callAccept.style.display = 'none'

        // Đổi nút từ chối thành nút kết thúc
        callReject.style.display = 'flex'
        callReject.innerHTML = `
        <i class="fa-solid fa-phone"></i>
        <span>Kết thúc</span>
    `

        this.socket.emit('call_request', {
            caller_id: this.config.user.id,
            receiver_id: userId
        }
        )
    },

    showIncomingCall: function (callerId) {

        this.callState = 'ringing'
        this.callUserId = callerId
        this.setCallUserInfo(callerId)
        callOverlay.style.display = 'flex'

        $('.call_status').textContent = 'Cuộc gọi đến...'

        callReject.style.display = 'flex'
        callAccept.style.display = 'flex'

        callReject.innerHTML = `
        <i class="fa-solid fa-phone-slash"></i>
        <span>Từ chối</span>
    `
    },

    openActiveCallWindow: async function (userId) {

        this.setCallUserInfo(userId)

        this.callState = 'active'

        callOverlay.style.display = 'none'

        callWindow.style.display = 'flex'

        callWindow.classList.remove(
            'minimized'
        )

        $('.call_status').textContent =
            'Đang kết nối...'

        callAccept.style.display = 'none'

        callReject.style.display = 'flex'

        callReject.innerHTML = `
        <i class="fa-solid fa-phone"></i>
        <span>Kết thúc</span>
    `
        // WWeb rtc

        this.createPeerConnection()
        const stream =
            await this.getLocalStream()
        if (!stream) {
            this.endCall()
            return
        }
        this.addLocalTracks()
        this.startCallTimer()
    },

    handleEvent: function () {
        // ==================== TURN ON/OFF NOTIFICATION =======

        const closeNotification = () => {
            notificationMenu.classList.remove('open')
            notificationIcon.classList.remove('active')
        }

        notificationIcon.onclick = (e) => {
            e.stopPropagation();
            const isOpen = notificationMenu.classList.contains('open')

            if (
                notificationMenu.classList.contains('open')
            ) {
                closeNotification()
                return
            }
            notificationMenu.classList.add('open')
            notificationIcon.classList.add('active')
            this.loadFriendRequests()
        }

        notificationClose.onclick = (e) => {
            e.stopPropagation();
            closeNotification()
        }

        notificationMenu.onclick = (e) => {
            e.stopPropagation()
        }

        document.addEventListener('click', () => {
            closeNotification()
        })

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

            this.socket.emit('send_message', {

                conversation_id:
                    this.currentConversation.conversation_id,

                sender_id:
                    this.config.user.id,

                content: content

            })

            messageInput.value = ''
        }

        messageInput.onkeydown = (e) => {

            if (e.key !== 'Enter') {
                return
            }

            e.preventDefault()

            sendMessageBtn.click()
        }

        // ==================== SEND IMAGE =======================
        imageBtn.onclick = () => {
            imageInput.click()
        }

        imageInput.onchange = async () => {

            const image = imageInput.files[0]

            if (!image) {
                return
            }

            const oldStatus =
                chatBody.querySelectorAll('.message_status')

            oldStatus.forEach(status => {
                status.remove()
            })


            try {

                const compressedImage =
                    await this.compressImage(image)

                // Tạo URL tạm cho ảnh
                const previewUrl =
                    URL.createObjectURL(compressedImage)

                // Hiển thị ảnh ngay lập tức
                chatBody.insertAdjacentHTML(
                    'beforeend',
                    `
                <div class="message sent message_pending">

                    <div class="message_content">

                        <img
                            class="message_image"
                            src="${previewUrl}"
                            alt="Ảnh đang gửi"
                        >

                    </div>

                    <span class="message_status">
                        Đang gửi...
                    </span>

                </div>
            `
                )

                // Cuộn xuống cuối
                const lastMessage =
                    chatBody.lastElementChild

                if (lastMessage) {
                    lastMessage.scrollIntoView({
                        behavior: 'smooth',
                        block: 'end'
                    })
                }


                const formData =
                    new FormData()

                formData.append(
                    'conversation_id',
                    this.currentConversation.conversation_id
                )

                formData.append(
                    'sender_id',
                    this.config.user.id
                )

                formData.append(
                    'image',
                    compressedImage
                )


                const response = await fetch(
                    `${API_URL}/api/messages`,
                    {
                        method: 'POST',
                        body: formData
                    }
                )

                const result =
                    await response.json()


                if (!result.success) {

                    console.error(
                        result.message
                    )

                    return
                }


                // Upload thành công
                await this.loadMessages(
                    this.currentConversation.conversation_id
                )

                await this.loadConversations()


                // Giải phóng URL tạm
                URL.revokeObjectURL(
                    previewUrl
                )

                imageInput.value = ''


            } catch (error) {

                console.error(
                    'Lỗi gửi ảnh:',
                    error
                )

            }
        }

        // ===================== SEND FILE ===========================
        fileBtn.onclick = () => {
            fileInput.click()
        }

        fileInput.onchange = async () => {

            const file =
                fileInput.files[0]

            if (!file) {
                return
            }

            const oldStatus =
                chatBody.querySelectorAll('.message_status')

            oldStatus.forEach(status => {
                status.remove()
            })


            const maxSize =
                60 * 1024 * 1024

            if (file.size > maxSize) {

                console.log(
                    'File quá lớn'
                )

                fileInput.value = ''

                return
            }

            if (!this.currentConversation) {
                return
            }

            // Tạo message tạm
            const pendingMessage = document.createElement('div')

            pendingMessage.className =
                'message sent message_pending'

            pendingMessage.innerHTML = `
        <div class="message_content">

            <div class="message_file">

                <i class="fa-regular fa-file"></i>

                <span>
                    ${file.name}
                </span>

            </div>

        </div>

        <span class="message_status">
            Đang gửi...
        </span>
    `

            chatBody.appendChild(
                pendingMessage
            )

            // Cuộn xuống cuối
            pendingMessage.scrollIntoView({
                behavior: 'smooth',
                block: 'end'
            })

            try {

                const formData =
                    new FormData()

                formData.append(
                    'conversation_id',
                    this.currentConversation.conversation_id
                )

                formData.append(
                    'sender_id',
                    this.config.user.id
                )

                formData.append(
                    'file',
                    file
                )

                console.log(
                    'Đang upload:',
                    file.name
                )

                const response =
                    await fetch(
                        `${API_URL}/api/messages`,
                        {
                            method: 'POST',
                            body: formData
                        }
                    )

                const result =
                    await response.json()

                if (!result.success) {

                    console.error(
                        result.message
                    )

                    pendingMessage
                        .querySelector('.message_status')
                        .textContent = 'Gửi thất bại'

                    return
                }

                console.log(
                    'Upload file thành công'
                )

                // Xóa message tạm
                pendingMessage.remove()
                // Hiển thị file thật ngay lập tức
                this.appendMessage(result.message)

                // Cập nhật preview cuộc trò chuyện
                this.updateConversationPreview(result.message)
                // Chưa load lại messages/conversations
                fileInput.value = ''

            } catch (error) {

                console.error(
                    'Lỗi gửi file:',
                    error
                )

                pendingMessage
                    .querySelector('.message_status')
                    .textContent = 'Gửi thất bại'

            }
        }

        // ==================== VOICE MESSAGE ====================

        voiceBtn.onclick = async () => {

            if (!this.currentConversation) {
                return
            }

            if (!this.isRecording) {

                try {

                    const stream =
                        await navigator.mediaDevices.getUserMedia({
                            audio: true
                        })

                    this.audioChunks = []

                    this.mediaRecorder =
                        new MediaRecorder(stream)

                    this.mediaRecorder.ondataavailable =
                        (event) => {

                            if (event.data.size > 0) {
                                this.audioChunks.push(
                                    event.data
                                )
                            }
                        }

                    this.mediaRecorder.onstop = async () => {

                        stream
                            .getTracks()
                            .forEach(track => track.stop())

                        console.log(
                            'Đã dừng ghi âm'
                        )

                        // Tạo file audio từ dữ liệu đã ghi
                        const audioBlob = new Blob(
                            this.audioChunks,
                            {
                                type: 'audio/webm'
                            }
                        )

                        // Tạo tên file
                        const audioFile = new File(
                            [audioBlob],
                            `voice_${Date.now()}.webm`,
                            {
                                type: 'audio/webm'
                            }
                        )

                        console.log(
                            'File voice:',
                            audioFile
                        )

                        try {

                            const formData = new FormData()

                            formData.append(
                                'conversation_id',
                                this.currentConversation.conversation_id
                            )

                            formData.append(
                                'sender_id',
                                this.config.user.id
                            )

                            formData.append(
                                'voice',
                                audioFile
                            )

                            console.log(
                                'Đang upload voice...'
                            )

                            const response = await fetch(
                                `${API_URL}/api/messages`,
                                {
                                    method: 'POST',
                                    body: formData
                                }
                            )

                            const result =
                                await response.json()

                            if (!result.success) {

                                console.error(
                                    'Gửi voice thất bại:',
                                    result.message
                                )

                                return
                            }

                            // console.log(
                            //     'Upload voice thành công:',
                            //     result.message
                            // )

                            // Hiển thị voice ngay lập tức
                            await this.loadMessages(
                                this.currentConversation.conversation_id
                            )

                            await this.loadConversations()

                        } catch (error) {

                            console.error(
                                'Lỗi gửi voice:',
                                error
                            )
                        }
                    }

                    this.mediaRecorder.start()

                    this.isRecording = true

                    voiceBtn.innerHTML =
                        '<i class="fa-solid fa-stop"></i>'

                    console.log(
                        'Đang ghi âm...'
                    )

                } catch (error) {

                    console.error(
                        'Không thể sử dụng microphone:',
                        error
                    )

                }

            } else {

                this.mediaRecorder.stop()

                this.isRecording = false

                voiceBtn.innerHTML =
                    '<i class="fa-solid fa-microphone"></i>'
            }
        }

        messageInput.addEventListener('input', () => {
            if (
                !this.currentConversation ||
                !this.socket
            ) {
                return
            }

            const conversationId =
                this.currentConversation.conversation_id

            if (!this.isTyping) {

                this.isTyping = true

                this.socket.emit(
                    'typing',
                    {
                        conversation_id:
                            conversationId,

                        user_id:
                            this.config.user.id
                    }
                )
            }

            clearTimeout(
                this.typingTimeout
            )

            this.typingTimeout =
                setTimeout(() => {
                    this.isTyping = false
                    this.socket.emit(
                        'stop_typing',
                        {
                            conversation_id:
                                conversationId,

                            user_id:
                                this.config.user.id
                        }
                    )

                }, 1000)
        }
        )
        // ============================== call popup ==============

        callBtn.onclick = () => {

            if (!this.currentConversation) {
                return
            }

            this.callUser(
                this.currentConversation.user.id
            )
        }

        callClose.onclick = () => {
            // Người gọi bấm X → kết thúc cuộc gọi
            if (this.callState === 'calling') {
                this.endCall()
                return
            }
            // Người nhận bấm X → từ chối
            if (this.callState === 'ringing') {
                this.socket.emit(
                    'call_reject',
                    {
                        caller_id: this.callUserId,
                        receiver_id: this.config.user.id
                    }
                )
            }
        }

        callReject.onclick = () => {

            if (this.callState === 'calling') {
                this.endCall()
                return
            }

            if (this.callState === 'ringing') {
                this.socket.emit(
                    'call_reject',
                    {
                        caller_id: this.callUserId,
                        receiver_id: this.config.user.id
                    }
                )
            }
        }

        // ===================== CALL & CALL video ================

        callMinimize.onclick = () => {

            callWindow.classList.toggle(
                'minimized'
            )
        }

        callMic.onclick = () => {

            this.isMicOn =
                !this.isMicOn

            if (this.localStream) {

                this.localStream
                    .getAudioTracks()
                    .forEach(track => {
                        track.enabled = this.isMicOn
                    }
                )
            }

            callMic.innerHTML =this.isMicOn
                    ? '<i class="fa-solid fa-microphone"></i>'
                    : '<i class="fa-solid fa-microphone-slash"></i>'

            callMic.classList.toggle('off',!this.isMicOn
            )

            callMic.title = this.isMicOn
                    ? 'Tắt microphone'
                    : 'Bật microphone'
        }

        callVideo.onclick = () => {

            this.isVideoOn =
                !this.isVideoOn

            callVideo.innerHTML =
                this.isVideoOn
                    ? '<i class="fa-solid fa-video"></i>'
                    : '<i class="fa-solid fa-video-slash"></i>'

            callVideo.classList.toggle(
                'off',
                !this.isVideoOn
            )
        }

        callEnd.onclick = () => {
            this.endCall()
        }

        callAccept.onclick = async () => {

            if (this.callState !== 'ringing') {
                return
            }

            this.socket.emit(
                'call_accept',
                {
                    caller_id: this.callUserId,
                    receiver_id: this.config.user.id
                }
            )

            await this.openActiveCallWindow(
                this.callUserId
            )
        }
    },

    start: function () {

        this.loadUser()
        this.socket = io(SOCKET_URL)

        this.socket.on('connect', () => {
            console.log('Đã kết nối Socket.IO:', this.socket.id)

            this.socket.emit('user_online', {
                user_id: this.config.user.id
            })
        })

        this.socket.on('disconnect', () => {
            console.log('Đã ngắt kết nối Socket.IO')
        })

        this.socket.on('profile_updated', (data) => {

            const userId = String(data.user_id)

            const username = data.username
            const avatar = data.avatar

            // Cập nhật tên và avatar trong danh sách conversation
            const conversationItems =
                document.querySelectorAll('.conversation_item')

            conversationItems.forEach(item => {

                const conversationId =
                    item.dataset.conversationId

                const conversation =
                    this.conversations.find(
                        conversation =>
                            String(conversation.conversation_id) ===
                            String(conversationId)
                    )

                if (!conversation) {
                    return
                }

                if (
                    String(conversation.user.id) !==
                    userId
                ) {
                    return
                }

                if (username) {

                    conversation.user.username =
                        username

                    const name =
                        item.querySelector(
                            '.conversation_name'
                        )

                    if (name) {
                        name.textContent = username
                    }
                }

                if (avatar) {

                    conversation.user.avatar =
                        avatar

                    const avatarElement =
                        item.querySelector(
                            '.conversation_avatar img'
                        )

                    if (avatarElement) {
                        avatarElement.src =
                            `${API_URL}${avatar}?t=${Date.now()}`
                    }
                }
            })

            // Nếu đang mở cuộc trò chuyện với người này
            if (
                this.currentConversation &&
                String(
                    this.currentConversation.user.id
                ) === userId
            ) {

                if (username) {

                    this.currentConversation.user.username =
                        username

                    chatUserName.textContent =
                        username
                }

                if (avatar) {

                    this.currentConversation.user.avatar =
                        avatar

                    chatAvatar.src =
                        `${API_URL}${avatar}?t=${Date.now()}`

                    const messageAvatars =
                        chatBody.querySelectorAll(
                            '.message_avatar'
                        )

                    messageAvatars.forEach(
                        messageAvatar => {
                            messageAvatar.src =
                                `${API_URL}${avatar}?t=${Date.now()}`
                        }
                    )
                }


            }
        })

        // Người dùng online / offline 
        this.socket.on('user_online', (data) => {

            if (!this.currentConversation) {
                return
            }

            if (
                String(data.user_id) ===
                String(this.currentConversation.user.id)
            ) {

                chatUserStatus.textContent =
                    'Đang hoạt động'
            }
        })

        this.socket.on('user_offline', (data) => {

            if (!this.currentConversation) {
                return
            }

            if (
                String(data.user_id) ===
                String(this.currentConversation.user.id)
            ) {

                chatUserStatus.textContent =
                    'Đang ngoại tuyến'
            }
        })

        this.socket.on('user_online_status', (data) => {

            if (!this.currentConversation) {
                return
            }

            if (
                String(data.user_id) !==
                String(this.currentConversation.user.id)
            ) {
                return
            }

            chatUserStatus.textContent =
                data.is_online
                    ? 'Đang hoạt động'
                    : 'Đang ngoại tuyến'
        })


        this.socket.on('new_message', async (message) => {

            console.log(
                'Nhận tin nhắn realtime:',
                message
            )

            const isCurrentConversation =
                this.currentConversation &&
                String(
                    this.currentConversation.conversation_id
                ) ===
                String(message.conversation_id)

            this.updateConversationPreview(message)

            // Tin nhắn của người khác
            if (
                String(message.sender_id) !==
                String(this.config.user.id)
            ) {

                // Đang mở đúng conversation
                if (isCurrentConversation) {

                    this.socket.emit(
                        'message_seen',
                        {
                            conversation_id:
                                message.conversation_id,

                            user_id:
                                this.config.user.id
                        }
                    )

                }

            }

            // Chỉ load lại nếu đang ở conversation đó
            if (isCurrentConversation) {

                await this.loadMessages(
                    this.currentConversation.conversation_id
                )
            }

        })

        this.socket.on('friend_accepted', () => {

            this.loadConversations()

        })

        this.socket.on('message_status', (data) => {

            console.log(
                'Status tin nhắn:',
                data
            )

            if (!this.currentConversation) {
                return
            }

            if (
                String(data.conversation_id) !==
                String(
                    this.currentConversation.conversation_id
                )
            ) {
                return
            }

            this.loadMessages(
                this.currentConversation.conversation_id
            )

        })

        // CALL 

        this.socket.on('incoming_call', (data) => {
            this.showIncomingCall(data.caller_id)
        }
        )

        this.socket.on('call_rejected', () => {

            this.stopCallTimer()

            this.callState = 'idle'
            this.callUserId = null

            callOverlay.style.display = 'none'
            callWindow.style.display = 'none'

            callWindow.classList.remove(
                'minimized'
            )

            callAccept.style.display = 'flex'
            callReject.style.display = 'flex'

            callReject.innerHTML = `
        <i class="fa-solid fa-phone-slash"></i>
        <span>Từ chối</span>
    `
        })

        this.socket.on('call_accepted', async (data) => {

            await this.openActiveCallWindow(data.user_id)
            await this.createOffer()

        })

        this.socket.on('call_cancelled', async () => {
            this.cleanupWebRTC()
            this.stopCallTimer()

            this.callState = 'idle'
            this.callUserId = null

            this.closeCallPopup()

            callWindow.style.display = 'none'
            callWindow.classList.remove('minimized')

            callAccept.style.display = 'flex'
            callReject.style.display = 'flex'

            callReject.innerHTML = `
        <i class="fa-solid fa-phone-slash"></i>
        <span>Từ chối</span>
    `

            await this.loadConversations()

            if (this.currentConversation) {

                await this.loadMessages(
                    this.currentConversation.conversation_id
                )
            }
        })

        this.socket.on('call_timeout', async () => {
            this.cleanupWebRTC()
            this.stopCallTimer()

            this.callState = 'idle'
            this.callUserId = null

            this.closeCallPopup()

            callWindow.style.display = 'none'
            callWindow.classList.remove('minimized')

            callAccept.style.display = 'flex'
            callReject.style.display = 'flex'

            callReject.innerHTML = `
        <i class="fa-solid fa-phone-slash"></i>
        <span>Từ chối</span>
    `

            await this.loadConversations()

            if (this.currentConversation) {

                await this.loadMessages(
                    this.currentConversation.conversation_id
                )
            }
        })

        this.socket.on('call_busy', (data) => {

            console.log(
                data.message
            )

            this.stopCallTimer()

            this.callState = 'idle'
            this.callUserId = null

            this.closeCallPopup()

            callWindow.style.display = 'none'
            callWindow.classList.remove('minimized')

        })

        this.socket.on('call_ended', () => {
            this.cleanupWebRTC()
            this.stopCallTimer()

            this.callState = 'idle'
            this.callUserId = null

            // Đóng popup cuộc gọi
            callOverlay.style.display = 'none'

            // Đóng cửa sổ cuộc gọi
            callWindow.style.display = 'none'
            callWindow.classList.remove('minimized')

            // Reset nút popup
            callAccept.style.display = 'flex'
            callReject.style.display = 'flex'

            callReject.innerHTML = `
        <i class="fa-solid fa-phone-slash"></i>
        <span>Từ chối</span>
    `
        })

        this.socket.on('webrtc_offer', async (data) => {
            if (!this.peerConnection) {
                return
            }

            try {

                await this.peerConnection
                    .setRemoteDescription(
                        new RTCSessionDescription(
                            data.offer
                        )
                    )

                console.log(
                    'Đã nhận WebRTC offer'
                )

                for (
                    const candidate
                    of this.pendingIceCandidates
                ) {

                    await this.handleIceCandidate(
                        candidate
                    )
                }

                this.pendingIceCandidates = []

                await this.createAnswer()

            } catch (error) {

                console.error(
                    'Không thể xử lý WebRTC offer:',
                    error
                )
            }
        }
        )

        this.socket.on('webrtc_answer', async (data) => {

            if (!this.peerConnection) {
                return
            }

            try {

                await this.peerConnection
                    .setRemoteDescription(
                        new RTCSessionDescription(
                            data.answer
                        )
                    )

                console.log(
                    'Đã nhận WebRTC answer'
                )

            } catch (error) {

                console.error(
                    'Không thể xử lý WebRTC answer:',
                    error
                )
            }
        }
        )

        this.socket.on('webrtc_ice_candidate', async (data) => {

            await this.handleIceCandidate(
                data.candidate
            )
        }
        )

        if (!this.checkLogin()) {
            return
        }

        this.handleEvent()
        // Kiểm tra lời mời ngay khi mở trang
        this.loadFriendRequests()
        this.loadConversations()
        setInterval(() => { this.loadFriendRequests() }, 10000)
    }
}

chatApp.start()