import React, { useState, ChangeEvent } from "react";
import { extractData } from "../core";

interface DecryptPageProps {
  onComplete?: (success: boolean) => void;
}

const DecryptPage: React.FC<DecryptPageProps> = ({ onComplete }) => {
  const [stegoImage, setStegoImage] = useState<string | null>(null);
  const [stegoKey, setStegoKey] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [extractedFile, setExtractedFile] = useState<{
    name: string;
    type: string;
    size: string;
  } | null>(null);
  const [imageDimensions, setImageDimensions] = useState<null | {
    width: number;
    height: number;
  }>(null);
  const [imageDataArray, setImageDataArray] =
    useState<Uint8ClampedArray<ArrayBufferLike> | null>(null);

  const [resultFileBlob, setResultFileBlob] = useState<null | Blob>(null);

  const handleImageUpload = (e: ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = (event: ProgressEvent<FileReader>) => {
        if (event.target?.result) {
          // Store the data URL for display
          setStegoImage(event.target.result as string);

          // Convert to image data array
          const img = new Image();
          img.onload = () => {
            // Create canvas
            const canvas = document.createElement("canvas");
            canvas.width = img.width;
            canvas.height = img.height;
            console.table({
              width: img.width,
              height: img.height,
            });

            // Draw image on canvas
            const ctx = canvas.getContext("2d");
            if (ctx) {
              ctx.drawImage(img, 0, 0);

              // Extract image data as Uint8ClampedArray
              const imageData = ctx.getImageData(
                0,
                0,
                canvas.width,
                canvas.height
              );

              // Store the dimensions and image data for later use
              setImageDimensions({
                width: img.width,
                height: img.height,
              });
              console.log(imageData.data);
              setImageDataArray(imageData.data);
            }

            // Reset any previous extraction
            setIsComplete(false);
          };

          // Load the image
          img.src = event.target.result as string;
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDecrypt = (): void => {
    if (!stegoImage || !stegoKey || !imageDataArray) return;

    setIsProcessing(true);

    const { blob, fileName } = extractData(imageDataArray, stegoKey);

    const customFileName = window.prompt("Save file as:", fileName);

    const finalFileName = customFileName || fileName;

    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = finalFileName;

    document.body.appendChild(a);
    a.click();
    setIsProcessing(false);
  };

  return (
    <div className="w-full bg-base-100 rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-6 text-center">
        Extract Hidden Files
      </h2>

      <div className="form-control mb-4">
        <label className="label">
          <span className="label-text">Upload image with hidden content</span>
        </label>
        <input
          type="file"
          className="file-input file-input-bordered w-full"
          accept="image/*"
          onChange={handleImageUpload}
        />
      </div>

      {stegoImage && (
        <div className="mt-4 mb-4 p-2 border rounded-lg bg-base-200">
          <img
            src={stegoImage}
            alt="Steganographic image"
            className="mx-auto max-h-48 object-contain"
          />
        </div>
      )}

      <div className="form-control mb-6">
        <label className="label">
          <span className="label-text">Stego-key</span>
        </label>
        <input
          type="password"
          placeholder="Enter decryption key"
          className="input input-bordered w-full"
          value={stegoKey}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setStegoKey(e.target.value)
          }
        />
      </div>

      <button
        className={`btn btn-primary w-full ${
          !stegoImage || !stegoKey ? "btn-disabled" : ""
        } ${isProcessing ? "loading" : ""}`}
        onClick={handleDecrypt}
        disabled={!stegoImage || !stegoKey || isProcessing}
      >
        {isProcessing ? "Decrypting..." : "Extract Hidden Content"}
      </button>

      {isComplete && extractedFile && (
        <div className="mt-6 p-4 border rounded-lg bg-base-200">
          <h3 className="font-bold mb-2">Extracted File:</h3>
          <div className="flex flex-col gap-1 mb-4">
            <p>
              <span className="font-semibold">Name:</span> {extractedFile.name}
            </p>
            <p>
              <span className="font-semibold">Type:</span> {extractedFile.type}
            </p>
            <p>
              <span className="font-semibold">Size:</span> {extractedFile.size}
            </p>
          </div>
          <button
            className="btn btn-outline btn-success w-full"
            onClick={handleDownload}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            Download File
          </button>
        </div>
      )}
    </div>
  );
};

export default DecryptPage;
