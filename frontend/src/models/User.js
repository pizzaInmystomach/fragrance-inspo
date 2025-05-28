import mongoose from 'mongoose';

const UserSchema = new mongoose.Schema({
    ID: {
        type: String,
        required: [true, '請輸入使用者ID'],
        unique: true
    },
    Email: {
        type: String,
        required: [true, '請輸入電子郵件帳號'],
        unique: true
    },
    Name: {
        type: String,
        required: [true, '請輸入使用者名稱'],
    },
    PasswordHash: {
        type: String,
        required: [true, '請輸入密碼'],
    },
    Phone: {
        type: String,
    },
    Favorite: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Collection',
    },
    IsBlocked: {
        type: Boolean,
        default: false,
    },
    LastLoginIP: {
        type: String,
    },
    LoginAttempts: {
        type: Number,
        default: 0,
    },
    createdDate: {
        type: Date,
        default: Date.now
    },
    lastInfoUpdatedDate: {
        type: Date,
        default: Date.now
    },
    lastLoggedIn: {
        type: Date,
    },
    Avatar: {
        type: String, // 用戶頭像的 URL
    },
    Birthday: {
        type: Date, // 生日
    },
    Gender: {
        type: String, // 性別
        enum: ['male', 'female', 'other'],
    },
    AccountStatus: {
        type: String, // 帳號狀態，如 active、suspended 等
        enum: ['active', 'suspended', 'disabled'],
        default: 'active',
    },
});

export default mongoose.models.User || mongoose.model('User', UserSchema);