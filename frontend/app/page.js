import Image from "next/image";

export default function Home() {
  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
        <h1 className="text-4xl font-bold text-center">
          Landing Page Shows Here
        </h1>
        <p className="text-lg text-center">
          Get started by editing&nbsp;
          <code className="font-mono font-bold">app/page.js</code>
        </p>
        <h1 className="text-4xl font-bold text-center">
          Collection Page: /library
        </h1>
        <p className="text-lg text-center">
          Get started by editing&nbsp;
          <code className="font-mono font-bold">app/(main-layout)/library/page.js</code>
        </p>
        <h1 className="text-4xl font-bold text-center">
          Chat Page: /chat
        </h1>
        <p className="text-lg text-center">
          Get started by editing&nbsp;
          <code className="font-mono font-bold">app/(main-layout)/chat/page.js</code>
        </p>
      </main>
    </div>
  );
}


