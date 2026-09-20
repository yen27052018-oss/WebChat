const avatarTool = {
    process: function (file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = function (e) {
                const img = new Image()
                img.onload = function () {

                    const size = 512
                    const canvas = document.createElement('canvas')
                    const ctx = canvas.getContext('2d')

                    canvas.width = size
                    canvas.height = size

                    // Lấy phần nhỏ nhất để cắt thành hình vuông
                    const minSize = Math.min(
                        img.width,
                        img.height
                    )

                    const sx = (img.width - minSize) / 2
                    const sy = (img.height - minSize) / 2

                    // Cắt + resize về 256x256
                    ctx.drawImage(
                        img,
                        sx,
                        sy,
                        minSize,
                        minSize,
                        0,
                        0,
                        size,
                        size
                    )
                    canvas.toBlob(
                        function (blob) {
                            if (!blob) {
                                reject(new Error(
                                    'Không thể xử lý ảnh'
                                ))
                                return
                            }
                            const newFile = new File(
                                [blob],`avatar_${Date.now()}.jpg`,
                                {
                                    type: 'image/jpeg'
                                }
                            )
                            resolve(newFile)
                        },'image/jpeg',0.98
                    )
                }
                img.onerror = function () {
                    reject(new Error(
                        'Không thể đọc ảnh'
                    ))
                }
                img.src = e.target.result
            }
            reader.onerror = function () {
                reject(new Error(
                    'Không thể đọc file'
                ))
            }
            reader.readAsDataURL(file)
        })
    }
}