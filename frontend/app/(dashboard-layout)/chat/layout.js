import ChatPageLayout from "@/components/chat/ChatPageLayout";

export default function ChatLayout({ children }) {
    return (
        <ChatPageLayout>
            {children}
        </ChatPageLayout>
    );
}