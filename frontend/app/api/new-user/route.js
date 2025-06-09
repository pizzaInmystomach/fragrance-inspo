// app/api/new-user/route.js
import { createUser } from "@/queries/user/createUser";
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

        const userData = {
            userID: data.userID,
            email: data.email,
            name: data.name,
            password: data.password,
        };

        const result = await createUser(userData);

        return new Response(JSON.stringify({ 
            success: true,
            message: 'User created successfully',
            userId: result.userId // 返回创建的用户ID
        }), {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
            },
        });
    } catch (error) {
        console.error('Error creating new user:', error);
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