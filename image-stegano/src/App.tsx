import { useState } from "react";
import "./App.css";
import EncryptPage from "./pages/Encrypt";
import DecryptPage from "./pages/Decrypt";

type EncryptionMode = "encrypt" | "decrypt";

function App() {
  const [activeMode, setActiveMode] = useState<EncryptionMode>("encrypt");
  return (
    <main className="w-full h-full flex flex-col items-start justify-center">
      <div className="tabs tabs-boxed mb-6">
        <button
          className={`tab tab-lg ${
            activeMode === "encrypt" ? "tab-active" : ""
          }`}
          onClick={() => setActiveMode("encrypt")}
        >
          Encrypt
        </button>
        <button
          className={`tab tab-lg ${
            activeMode === "decrypt" ? "tab-active" : ""
          }`}
          onClick={() => setActiveMode("decrypt")}
        >
          Decrypt
        </button>
      </div>

      {activeMode === "encrypt" ? <EncryptPage /> : <DecryptPage />}
    </main>
  );
}

export default App;
