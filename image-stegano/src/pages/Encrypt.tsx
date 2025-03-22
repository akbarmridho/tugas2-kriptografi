import React, { useState, ChangeEvent } from "react";
import {
  calculateMaxFileSizeBPCS,
  calculateMaxFileSizeLSB,
  calculatePSNR,
  hideDataBPCS,
  hideDataLSB,
} from "../core";

const EncryptPage: React.FC = () => {
  const [image, setImage] = useState<string | null>(null);
  const [stegoKey, setStegoKey] = useState<string>("");
  const [fileToEmbed, setFileToEmbed] = useState<{
    name: string;
    type: string;
    size: number;
    data: Uint8Array;
  } | null>(null);
  const [encryptMessage, setEncryptMessage] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [stegoResult, setStegoResult] = useState<string | null>(null);
  const [imageDimensions, setImageDimensions] = useState<null | {
    width: number;
    height: number;
  }>(null);
  const [imageDataArray, setImageDataArray] =
    useState<Uint8ClampedArray<ArrayBufferLike> | null>(null);
  const [maxFileSizes, setMaxFileSizes] = useState<null | {
    lsb: number;
    bpcs: number;
  }>(null);
  const [psnrValue, setPsnrValue] = useState<null | number>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<"lsb" | "bpcs">("lsb");
  const [threshold, setThreshold] = useState<number>(0.4);

  const handleImageUpload = (e: ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();

      reader.onload = (event: ProgressEvent<FileReader>) => {
        if (event.target?.result) {
          // Store the data URL for display
          setImage(event.target.result as string);

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

              // Calculate max file size that can be embedded
              const maxSizeLSB = calculateMaxFileSizeLSB(
                img.width,
                img.height,
                3,
                1
              );
              const maxSizeBPCS = calculateMaxFileSizeBPCS(
                img.width,
                img.height
              );
              setMaxFileSizes({
                lsb: maxSizeLSB,
                bpcs: maxSizeBPCS,
              });
            }

            // Reset any previous extraction
            setIsComplete(false);
            setFileToEmbed(null);
          };

          // Load the image
          img.src = event.target.result as string;
        }
      };

      reader.readAsDataURL(file);
    }
  };

  const handleSecretFileUpload = (e: ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();

      reader.onload = (event: ProgressEvent<FileReader>) => {
        if (event.target?.result) {
          if (!maxFileSizes) {
            return;
          }

          // Check if file size is within limits
          if (
            (selectedMethod === "lsb" && file.size > maxFileSizes.lsb) ||
            (selectedMethod === "bpcs" && file.size > maxFileSizes.bpcs)
          ) {
            setError(
              `File too large for ${selectedMethod.toUpperCase()} method. Max size in bytes: ${
                selectedMethod === "lsb" ? maxFileSizes.lsb : maxFileSizes.bpcs
              }`
            );
            return;
          } else {
            setError(null);
          }

          const fileData = new Uint8Array(event.target.result as ArrayBuffer);

          // Store file information
          const rawName = file.name.split(".");
          const extension = rawName[rawName.length - 1];
          setFileToEmbed({
            name: file.name,
            type: extension,
            size: file.size,
            data: fileData,
          });

          console.log(fileData);

          console.log(file.name);
          console.log(file.type);
        }
      };

      reader.readAsArrayBuffer(file);
    }
  };

  // Encode function
  const handleEncode = () => {
    setIsProcessing(true);
    if (!imageDataArray || !fileToEmbed || !stegoKey) {
      setError("Missing required inputs");
      setIsProcessing(false);
      return;
    }

    try {
      // Create a copy of the image data
      const imageData = new Uint8ClampedArray(imageDataArray);

      // Apply steganography based on selected method
      let modifiedImageData;
      console.log("Entering");
      if (selectedMethod === "lsb") {
        console.log("is LSB");
        modifiedImageData = hideDataLSB(
          imageData,
          fileToEmbed.data,
          stegoKey,
          1,
          {
            encrypted: encryptMessage,
            name: fileToEmbed.name,
            type: fileToEmbed.type,
          }
        );
      } else {
        modifiedImageData = hideDataBPCS(
          imageData,
          fileToEmbed.data,
          stegoKey,
          threshold ?? 0.4,
          {
            encrypted: encryptMessage,
            name: fileToEmbed.name,
            type: fileToEmbed.type,
          }
        );
      }

      if (!imageDimensions) {
        return;
      }

      // Calculate PSNR
      const psnr = calculatePSNR(imageDataArray, modifiedImageData);
      setPsnrValue(psnr);

      // Create canvas to display the modified image
      const canvas = document.createElement("canvas");
      canvas.width = imageDimensions.width;
      canvas.height = imageDimensions.height;

      const ctx = canvas.getContext("2d");
      if (ctx) {
        // Create ImageData object
        const modifiedImageDataObj = new ImageData(
          modifiedImageData,
          imageDimensions.width,
          imageDimensions.height
        );

        // Put the modified image data on the canvas
        ctx.putImageData(modifiedImageDataObj, 0, 0);

        // Convert canvas to data URL
        const dataURL = canvas.toDataURL("image/png");
        setStegoResult(dataURL);
        setIsComplete(true);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = (): void => {
    if (stegoResult) {
      const a = document.createElement("a");
      a.href = stegoResult;
      a.download = "stego-image.png";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  return (
    <div className="min-h-screen bg-base-200 flex gap-12 items-center justify-center w-full">
      <div className="w-full max-w-2xl p-8 bg-base-100 shadow-xl rounded-xl">
        <h1 className="text-3xl font-bold text-center mb-6">
          Image Steganography Tool
        </h1>

        <div className="divider">IMAGE</div>
        <div className="flex flex-col items-center mb-6">
          <div className="form-control w-full">
            <label className="label">
              <span className="label-text">Choose carrier image</span>
            </label>
            <input
              type="file"
              className="file-input file-input-bordered w-full"
              accept="image/*"
              onChange={handleImageUpload}
            />
          </div>

          {image && (
            <div className="mt-4 p-2 border rounded-lg w-full">
              <img
                src={image}
                alt="Uploaded"
                className="mx-auto max-h-64 object-contain"
              />
            </div>
          )}
        </div>

        <div className="divider">MESSAGE</div>
        <div className="form-control mb-6">
          <label className="label">
            <span className="label-text">Stego Key (max 25 characters)</span>
            <span className="label-text-alt">{stegoKey.length}/25</span>
          </label>
          <input
            type="text"
            placeholder="Enter stego key"
            className="input input-bordered w-full"
            maxLength={25}
            value={stegoKey}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setStegoKey(e.target.value)
            }
          />
        </div>

        <div className="form-control mb-6">
          <label className="label">
            <span className="label-text">Secret file to encode</span>
          </label>
          <input
            type="file"
            className="file-input file-input-bordered w-full"
            onChange={handleSecretFileUpload}
          />
          {fileToEmbed && (
            <label className="label">
              <span className="label-text-alt">
                Selected: {fileToEmbed.name}
              </span>
            </label>
          )}
        </div>
        <div className="tabs tabs-boxed mb-6">
          <button
            className={`tab tab-lg ${
              selectedMethod === "lsb" ? "tab-active" : ""
            }`}
            onClick={() => setSelectedMethod("lsb")}
          >
            LSB
          </button>
          <button
            className={`tab tab-lg ${
              selectedMethod === "bpcs" ? "tab-active" : ""
            }`}
            onClick={() => setSelectedMethod("bpcs")}
          >
            BPCS
          </button>
        </div>
        {selectedMethod === "bpcs" && (
          <div className="form-control mb-6">
            <label className="label">
              <span className="label-text">BPCS Threshold</span>
            </label>
            <input
              type="number"
              min={0}
              max={1}
              className="input"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
            />
          </div>
        )}

        <div>Max file size: {maxFileSizes?.[selectedMethod]} bytes</div>

        <div>{error}</div>

        <div className="form-control mb-6">
          <label className="label cursor-pointer justify-start gap-4">
            <input
              type="checkbox"
              className="toggle toggle-primary"
              checked={encryptMessage}
              onChange={() => setEncryptMessage(!encryptMessage)}
            />
            <span className="label-text">Encrypt message</span>
          </label>
        </div>

        <button
          className={`btn btn-primary w-full ${
            !image || (!stegoKey && !fileToEmbed) ? "btn-disabled" : ""
          } ${isProcessing ? "loading" : ""}`}
          onClick={handleEncode}
          disabled={
            !image ||
            (!stegoKey && !fileToEmbed) ||
            isProcessing ||
            error !== null
          }
        >
          {isProcessing
            ? "Processing..."
            : isComplete
            ? "Completed!"
            : "Encode Message"}
        </button>

        {isComplete && (
          <div className="mt-4 alert alert-success">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="stroke-current shrink-0 h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>Success! Your image has been encoded with your message.</span>
          </div>
        )}
      </div>
      {/* Output Section */}
      {stegoResult && (
        <div className="flex flex-col">
          <div className="divider">OUTPUT</div>
          <div className="flex flex-col items-center justify-center h-full">
            {!stegoResult && !isComplete && (
              <div className="text-center p-8 border border-dashed rounded-lg bg-base-200 w-full h-64 flex items-center justify-center"></div>
            )}
            <div className="p-2 border rounded-lg bg-base-200 w-full mb-4">
              <img
                src={stegoResult}
                alt="Result"
                className="mx-auto max-h-48 object-contain"
              />
            </div>
            <div>PSNR value: {psnrValue}</div>

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
              Download Image
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EncryptPage;
