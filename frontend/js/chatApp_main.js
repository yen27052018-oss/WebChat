const $ = document.querySelector.bind(document)
// const $$ = document.querySelectorAll.bind(document)

const LOGIN_STORAGE_KEY = 'CHAT_WATCH_LOGIN'

const userName = $('#user_name')
const userAvt = $('#user_avt')
const profileName = $('#profile_name')

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
const addFriendBtn = $('#addFriendBtn')
const addfrModal = $('#addfrModal')
const closeAddFriend = $('#closeAddFriend')

const friendUserSearch = $('#friendUserSearch')
const searchFriendBtn = $('#searchFriendBtn')
const friendSearchResult = $('#friendSearchResult')

const notificationIcon = $('#notification_btn')
const notificationMenu = $('.notification_menu')
const notificationClose = $('#closeNotif')

const chatApp = {
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
                    `http://127.0.0.1:5000${this.config.user.avatar}`
            }
        }
    },

    openProfile: function () {
        profileName.value = this.config.user.username

        if (
            !this.config.user.avatar ||
            this.config.user.avatar === 'default_avt.png'
        ) {
            profileAvt.src = './assests/img/default_avt.png'
        } else {
            profileAvt.src =
                `http://127.0.0.1:5000${this.config.user.avatar}`
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


    handleEvent: function () {
        // ==================== TURN ON/OFF NOTIFICATION =======
        notificationIcon.onclick = (e) => {
            e.stopPropagation();
            notificationMenu.classList.add('open')
        }

        notificationClose.onclick = (e) => {
             e.stopPropagation();
            notificationMenu.classList.remove('open')
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

        profileModal.onclick = (e) => {
            if (e.target === profileModal) {
                this.closeProfile()
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
                    'http://127.0.0.1:5000/api/change-password',
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

        avatarInput.onchange = (e) => {
            const file = e.target.files[0]

            if (file) {
                profileAvt.src = URL.createObjectURL(file)
            }
        }

        // ==================== SAVE PROFILE ====================

        saveProfile.onclick = async () => {
            const newUsername = profileName.value.trim()
            const oldUsername = this.config.user.username
            const avatarFile = avatarInput.files[0]

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
                        'http://127.0.0.1:5000/api/update-profile',
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
                        'http://127.0.0.1:5000/api/update-avatar',
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
                        `http://127.0.0.1:5000${result.avatar}`

                    profileAvt.src =
                        `http://127.0.0.1:5000${result.avatar}`
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

        addFriendBtn.onclick = () => {
            addfrModal.classList.add('active')
        }

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
                    `http://127.0.0.1:5000/api/search-user?keyword=${encodeURIComponent(keyword)}&userid=${this.config.user.userid}`
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
                            : `http://127.0.0.1:5000${user.avatar}`

                    return `
                            <div class="modal_item">
                                <img src="${avatar}" alt="">

                                <div class="modal_container">
                                    <h4 class="modal_name">${user.username}</h4>
                                    <p class="modal_id">${user.userid}</p>
                                </div>

                                <button type="button" class="btn btn_addfriend">
                                    Kết bạn
                                </button>
                            </div>
                        `
                }).join('')
            } catch (error) {
                console.error(error)
                friendSearchResult.innerHTML = `
                <div class="modal_empty">
                    <p>Không thể kết nối đến máy chủ</p>
                </div>`
            }
        }
    },

    start: function () {
        if (!this.checkLogin()) {
            return
        }

        this.loadUser()
        this.handleEvent()
    }
}

chatApp.start()