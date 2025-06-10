import clientPromise from "@/lib/mongodb";
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import User from "@/models/User";

export const loginUser = async (data) => {
    const client = await clientPromise;
    const db = client.db('fragrance_inspo_app_db');
    const user_collection = db.collection('users');

    const {
        email,
        password
    } = data;

    try {
        // 查找用戶是否存在
        const existingUser = await user_collection.findOne({ Email: email });
        
        if (!existingUser) {
            return {
                status: 404,
                message: 'User not found'
            };
        }

        // 檢查帳號狀態
        if (existingUser.AccountStatus === 'suspended' || existingUser.AccountStatus === 'disabled') {
            return {
                status: 403,
                message: 'Account is suspended or disabled'
            };
        }

        // 檢查是否被封鎖
        if (existingUser.IsBlocked) {
            return {
                status: 403,
                message: 'Account is blocked'
            };
        }

        // 驗證密碼
        const isPasswordValid = await bcrypt.compare(password, existingUser.PasswordHash);
        
        if (!isPasswordValid) {
            // 增加登入失敗次數
            await user_collection.updateOne(
                { Email: email },
                { 
                    $inc: { LoginAttempts: 1 },
                    $set: { lastInfoUpdatedDate: new Date() }
                }
            );

            // 如果登入失敗次數超過5次，封鎖帳號
            if (existingUser.LoginAttempts + 1 >= 5) {
                await user_collection.updateOne(
                    { Email: email },
                    { 
                        $set: { 
                            IsBlocked: true,
                            lastInfoUpdatedDate: new Date()
                        }
                    }
                );
                return {
                    status: 403,
                    message: 'Account blocked due to multiple failed login attempts'
                };
            }

            return {
                status: 401,
                message: 'Invalid password'
            };
        }

        // 登入成功，重置登入失敗次數並更新最後登入時間
        const clientIP = data.clientIP || 'unknown';
        await user_collection.updateOne(
            { Email: email },
            { 
                $set: { 
                    LoginAttempts: 0,
                    lastLoggedIn: new Date(),
                    LastLoginIP: clientIP,
                    lastInfoUpdatedDate: new Date()
                }
            }
        );

        // 生成 JWT token
        const tokenPayload = {
            userID: existingUser.ID,
            email: existingUser.Email,
            name: existingUser.Name
        };

        const token = jwt.sign(
            tokenPayload,
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );

        // 準備返回的用戶資料（不包含敏感資訊）
        const userData = {
            id: existingUser.ID,
            email: existingUser.Email,
            name: existingUser.Name,
            phone: existingUser.Phone,
            avatar: existingUser.Avatar,
            birthday: existingUser.Birthday,
            gender: existingUser.Gender,
            accountStatus: existingUser.AccountStatus,
            createdDate: existingUser.createdDate,
            lastLoggedIn: new Date()
        };

        return {
            status: 200,
            message: 'Login successful',
            token,
            user: userData
        };

    } catch (error) {
        console.error('Error during user login:', error);
        return {
            status: 500,
            message: error.message || 'Failed to login user'
        };
    }
};

// 驗證 JWT token 的函數
export const verifyUserToken = async (token) => {
    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        
        const client = await clientPromise;
        const db = client.db('fragrance_inspo_app_db');
        const user_collection = db.collection('users');

        // 驗證用戶是否仍然存在且狀態正常
        const user = await user_collection.findOne({ 
            ID: decoded.userID,
            AccountStatus: 'active',
            IsBlocked: false
        });

        if (!user) {
            return {
                status: 401,
                message: 'Invalid token or user not found'
            };
        }

        const userData = {
            id: user._id,
            userID: user.ID,
            email: user.Email,
            name: user.Name,
            phone: user.Phone,
            avatar: user.Avatar,
            birthday: user.Birthday,
            gender: user.Gender,
            accountStatus: user.AccountStatus,
            createdDate: user.createdDate,
            lastLoggedIn: user.lastLoggedIn
        };

        return {
            status: 200,
            message: 'Token is valid',
            user: userData
        };

    } catch (error) {
        console.error('Error verifying token:', error);
        
        if (error.name === 'TokenExpiredError') {
            return {
                status: 401,
                message: 'Token has expired'
            };
        } else if (error.name === 'JsonWebTokenError') {
            return {
                status: 401,
                message: 'Invalid token'
            };
        }

        return {
            status: 500,
            message: 'Failed to verify token'
        };
    }
};

// 登出函數（可選，用於記錄登出時間）
export const logoutUser = async (userID) => {
    try {
        const client = await clientPromise;
        const db = client.db('fragrance_inspo_app_db');
        const user_collection = db.collection('users');

        await user_collection.updateOne(
            { ID: userID },
            { 
                $set: { 
                    lastInfoUpdatedDate: new Date()
                }
            }
        );

        return {
            status: 200,
            message: 'Logout successful'
        };

    } catch (error) {
        console.error('Error during user logout:', error);
        return {
            status: 500,
            message: error.message || 'Failed to logout user'
        };
    }
};