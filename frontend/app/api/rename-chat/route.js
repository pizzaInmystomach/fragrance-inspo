// app/api/store-admin/categories/route.js
import { renameChat } from '@/queries/chat/renameChat';
import { NextResponse } from "next/server";
import { v4 as uuidv4 } from 'uuid';

// 创建新类别
export async function POST(req) {
    try {

        const data = await req.json();

        // 验证 JWT 并获取商家信息
        // const merchantSession = await getMerchantFromRequest(req);
        // const { accountID } = merchantSession;
        // console.log(merchantSession);

        // 添加商店 ID 到类别数据
        const renameChatData = {
            userID: data.userID,
            chatID: data.chatID,
            newTitle: data.newTitle
        };

        const result = await renameChat(renameChatData);

        return new Response(JSON.stringify({ message: 'Chat renamed', result }), {
            status: 200,
            headers:{
                'Content-Type': 'application/json',
            },
        })
    } catch (error) {
        console.error('Error creating new chat:', error);
        return new Response(JSON.stringify({ message: error.message }), {
            status: 400,
            headers: {
              'Content-Type': 'application/json',
            },
          });
    }
}

// // 获取单个类别
// export async function GETById(request, { params }) {
//   const { id } = params;
//   const category = categories.find(cat => cat.id === id);
//   if (!category) return NextResponse.json({ message: 'Category not found' }, { status: 404 });
//   return NextResponse.json(category);
// }



// // 删除类别
// export async function DELETE(request, { params }) {
//   const { id } = params;
//   const categoryIndex = categories.findIndex(cat => cat.id === id);
//   if (categoryIndex === -1) return NextResponse.json({ message: 'Category not found' }, { status: 404 });

//   categories.splice(categoryIndex, 1);
//   return NextResponse.json({ message: 'Category deleted' });
// }