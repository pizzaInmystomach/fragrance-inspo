import mongoose, { mongo } from 'mongoose';

const ChatSchema = new mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
    },
    chatId: {
        type: String,
        unique: true,
        required: true
    },
    title: {
        type: String,
        required: true
    },
    messages: [
        {
            sender: {
                type: String,
                enum: ['user', 'bot'],
                required: true
            },
            content: {
                type: String,
                required: true
            },
            timestamp: {
                type: Date,
                default: Date.now
            }
        }
    ],
    recommendedFragrances: [
        {
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Fragrance'
        }
    ],
    createdAt: {
        type: Date,
        default: Date.now
    },
    updatedAt: {
        type: Date,
        default: Date.now
    },
    isDeleted: {
        type: Boolean,
        default: false
    },
    deletedAt: {
        type: Date,
        default: null
    }
});

export default mongoose.models.Chat || mongoose.model('Chat', ChatSchema);