'use client'
import { useSession } from 'next-auth/react'

export default function UserProfile() {
    const { data: session, status } = useSession()

    if (status === 'loading') {
        return (
            <div className="flex items-center justify-center p-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2">載入中...</span>
            </div>
        )
    }

    if (status === 'unauthenticated') {
        return (
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <p className="text-yellow-800">請先登入以查看用戶資料</p>
            </div>
        )
    }

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">用戶資料</h2>

            <div className="flex items-center space-x-4">
                <img
                    src={session.user.image}
                    alt="用戶頭像"
                    className="w-16 h-16 rounded-full border-2 border-gray-200"
                />
                <div>
                    <h3 className="text-lg font-medium text-gray-900">
                        {session.user.name}
                    </h3>
                    <p className="text-gray-600">
                        {session.user.email}
                    </p>
                </div>
            </div>
        </div>
    )
}