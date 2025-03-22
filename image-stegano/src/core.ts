const HEADER_SIZE = 64;

const CONSTANT = 7;

export type EncryptionMetadata = {
  name: string;
  type: string;
  encrypted: boolean;
};

export type Header = {
  fileSize: number;
  method: "LSB" | "BPCS";
  bitsPerChannel?: number;
  threshold?: number;
  isEncrypted: boolean;
  filename: string;
};

export function calculateMaxFileSizeLSB(
  width: number,
  height: number,
  channels: number = 3,
  bitsPerChannel: number = 1
): number {
  // Total available bits = width × height × channels × bitsPerChannel
  const totalBits = width * height * channels * bitsPerChannel;
  // Convert to bytes and subtract header size
  return Math.floor(totalBits / 8 - HEADER_SIZE);
}

export function calculateMaxFileSizeBPCS(
  width: number,
  height: number,
  channels: number = 3,
  threshold: number = 0.4
): number {
  const usableBitPlaneRatio = 1.0 - threshold;
  const bitsPerPixel = channels * 8; // 8 bits per channel
  const totalBits = width * height * bitsPerPixel * usableBitPlaneRatio;
  return Math.floor(totalBits / 8 - HEADER_SIZE);
}

function vigenereProcess(
  data: Uint8Array,
  key: string,
  encrypt: boolean = true
): Uint8Array {
  const result = new Uint8Array(data.length);

  // Convert key to byte array
  const keyBytes = new TextEncoder().encode(key);

  // Process each byte
  for (let i = 0; i < data.length; i++) {
    // Get key byte (cycling through the key)
    const keyByte = keyBytes[i % keyBytes.length];

    // Apply Vigenère cipher (addition for encryption, subtraction for decryption)
    if (encrypt) {
      // Add key byte value and wrap around if exceeds 255
      result[i] = (data[i] + keyByte) % 256;
    } else {
      // Subtract key byte value and handle underflow
      result[i] = (data[i] - keyByte + 256) % 256;
    }
  }

  return result;
}

export function hideDataLSB(
  imageData: Uint8ClampedArray,
  fileData: Uint8Array,
  key: string,
  bitsPerChannel: number = 1,
  metadata: EncryptionMetadata
): Uint8ClampedArray {
  // Validate inputs
  if (key.length > 25) {
    throw new Error("Stego-key must be exactly 25 characters long");
  }

  // Prepare seed from key for pseudo-random pixel selection
  const seed = createSeedFromKey(key);

  const fileDataToHide = metadata.encrypted
    ? vigenereProcess(fileData, key, true)
    : fileData;

  // Create header containing file size and other metadata
  const fileSize = fileDataToHide.length;
  const header = createHeader(
    fileSize,
    "LSB",
    bitsPerChannel,
    metadata.encrypted,
    metadata.name
  );

  console.log(header);

  // Combine header and file data
  const dataToHide = new Uint8Array(HEADER_SIZE + fileDataToHide.length);
  dataToHide.set(header, 0);
  dataToHide.set(fileDataToHide, HEADER_SIZE);

  // Create a copy of the image data to avoid modifying the original
  const modifiedImageData = new Uint8ClampedArray(imageData);

  // Calculate total bits needed
  const totalBitsNeeded = dataToHide.length * 8;

  // Check if the image is large enough
  const maxBits = Math.floor((imageData.length * bitsPerChannel) / 1); // Only use RGB channels, not alpha
  if (totalBitsNeeded > maxBits) {
    throw new Error("File too large to hide in this image");
  }

  // Use key to generate a sequence of pixel indices
  const pixelIndices = generatePixelIndices(
    seed,
    imageData.length / 4,
    totalBitsNeeded
  ); // Divide by 4 because RGBA

  // Embed data using LSB method
  let bitIndex = 0;

  for (let i = 0; i < dataToHide.length; i++) {
    const byte = dataToHide[i];

    // Process each bit in the byte
    for (let j = 7; j >= 0; j--) {
      if (bitIndex >= totalBitsNeeded) break;

      // Get the bit to hide
      const bit = (byte >> j) & 1;

      // Get pixel based on pseudo-random sequence
      const pixelIndex =
        pixelIndices[Math.floor(bitIndex / (3 * bitsPerChannel))];
      const baseIndex = pixelIndex * 4; // RGBA has 4 values per pixel

      // Determine which color channel to use based on bit position
      const channelOffset = Math.floor(
        (bitIndex % (3 * bitsPerChannel)) / bitsPerChannel
      );

      // Determine which bit in the channel to modify
      const bitOffset = bitIndex % bitsPerChannel;

      // Skip alpha channel (index 3)
      if (channelOffset < 3) {
        // Only RGB channels
        // Clear the target bit and set it to our data bit
        const mask = ~(1 << bitOffset);
        modifiedImageData[baseIndex + channelOffset] =
          (modifiedImageData[baseIndex + channelOffset] & mask) |
          (bit << bitOffset);
      }

      bitIndex++;
    }
  }

  return modifiedImageData;
}

export function extractData(imageData: Uint8ClampedArray, key: string) {
  // Validate key
  if (key.length > 25) {
    throw new Error("Stego-key must be exactly 25 characters long");
  }

  // Prepare seed from key
  const seed = createSeedFromKey(key);

  // First extract the header to get file size and parameters
  const header = new Uint8Array(HEADER_SIZE);

  // Generate initial pixel indices for header
  const headerPixelIndices = generatePixelIndices(
    seed,
    imageData.length / 4,
    HEADER_SIZE * 8
  );

  // Extract header
  let bitIndex = 0;
  for (let i = 0; i < HEADER_SIZE; i++) {
    let byte = 0;

    for (let j = 7; j >= 0; j--) {
      const pixelIndex = headerPixelIndices[Math.floor(bitIndex / 3)]; // Assuming 1 bit per channel
      const baseIndex = pixelIndex * 4;
      const channelOffset = bitIndex % 3; // Only using RGB channels

      // Extract the LSB
      const bit = imageData[baseIndex + channelOffset] & 1;
      byte |= bit << j;

      bitIndex++;
    }

    header[i] = byte;
  }

  // Parse the header
  const parsedHeader = parseHeader(header);
  const method = parsedHeader.method;
  console.log(parsedHeader);
  const result: Uint8Array =
    method === "BPCS"
      ? extractDataBPCS(imageData, key, parsedHeader, seed)
      : extractDataLSB(imageData, key, parsedHeader, seed);

  // Get file name and MIME type from header or determine them
  const fileName = parsedHeader.filename || "extracted_file";
  const mimeType = determineFileType(result, fileName);

  return {
    blob: new Blob([result], { type: mimeType }),
    fileName,
  };
}

function extractHeaderBPCS(imageData: Uint8ClampedArray, seed: number): Header {
  const width = Math.sqrt(imageData.length / 4); // Estimate width from RGBA data
  const height = width;
  const bitPlanes = extractBitPlanes(imageData, width, height);

  const initialThreshold = 0.4;
  const complexRegions = findComplexRegions(bitPlanes, initialThreshold);

  const shuffledRegions = shuffleComplexRegions(complexRegions, seed);

  const headerBits = HEADER_SIZE * 8;
  const bitsPerRegion = 8 * 8; // 8x8 block
  const regionsForHeader = Math.ceil(headerBits / bitsPerRegion);

  if (shuffledRegions.length < regionsForHeader) {
    throw new Error("Not enough complex regions to extract header");
  }

  const headerBlocks: boolean[][] = [];
  for (let i = 0; i < regionsForHeader; i++) {
    if (i >= shuffledRegions.length) break;

    const region = shuffledRegions[i];
    const block = extractBlockFromBitPlane(
      bitPlanes[region.plane],
      region.x,
      region.y
    );
    headerBlocks.push(block);
  }

  const headerData = convertBlocksToData(headerBlocks, HEADER_SIZE);

  return parseHeader(headerData);
}

function determineFileType(data: Uint8Array, fileName?: string): string {
  if (fileName) {
    const extension = fileName.split(".").pop()?.toLowerCase();

    if (extension) {
      const mimeTypes: Record<string, string> = {
        jpg: "image/jpeg",
        jpeg: "image/jpeg",
        png: "image/png",
        gif: "image/gif",
        bmp: "image/bmp",
        webp: "image/webp",
        pdf: "application/pdf",
        txt: "text/plain",
        html: "text/html",
        htm: "text/html",
        css: "text/css",
        js: "application/javascript",
        json: "application/json",
        xml: "application/xml",
        zip: "application/zip",
        doc: "application/msword",
        docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        xls: "application/vnd.ms-excel",
        xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ppt: "application/vnd.ms-powerpoint",
        pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        mp3: "audio/mpeg",
        mp4: "video/mp4",
        wav: "audio/wav",
        webm: "video/webm",
        ogg: "audio/ogg",
        csv: "text/csv",
      };

      if (mimeTypes[extension]) {
        return mimeTypes[extension];
      }
    }
  }

  if (data.length > 4) {
    // Check for PNG
    if (
      data[0] === 0x89 &&
      data[1] === 0x50 &&
      data[2] === 0x4e &&
      data[3] === 0x47
    ) {
      return "image/png";
    }

    // Check for JPEG
    if (data[0] === 0xff && data[1] === 0xd8 && data[2] === 0xff) {
      return "image/jpeg";
    }

    // Check for GIF
    if (data[0] === 0x47 && data[1] === 0x49 && data[2] === 0x46) {
      return "image/gif";
    }

    // Check for PDF
    if (
      data[0] === 0x25 &&
      data[1] === 0x50 &&
      data[2] === 0x44 &&
      data[3] === 0x46
    ) {
      return "application/pdf";
    }

    // Check for ZIP
    if (
      data[0] === 0x50 &&
      data[1] === 0x4b &&
      data[2] === 0x03 &&
      data[3] === 0x04
    ) {
      return "application/zip";
    }
  }

  return "application/octet-stream";
}

export function extractDataLSB(
  imageData: Uint8ClampedArray,
  key: string,
  header: Header,
  seed: number
): Uint8Array {
  const fileSize = header.fileSize;
  const bitsPerChannel = header.bitsPerChannel ?? 1;

  const totalBitsNeeded = (HEADER_SIZE + fileSize) * 8;
  const pixelIndices = generatePixelIndices(
    seed,
    imageData.length / 4,
    totalBitsNeeded
  );
  const extractedData = new Uint8Array(header.fileSize);
  let bitIndex = HEADER_SIZE * 8; // Start after header

  for (let i = 0; i < header.fileSize; i++) {
    let byte = 0;

    for (let j = 7; j >= 0; j--) {
      const pixelIndex =
        pixelIndices[Math.floor(bitIndex / (3 * bitsPerChannel))];
      const baseIndex = pixelIndex * 4;

      const channelOffset = Math.floor(
        (bitIndex % (3 * bitsPerChannel)) / bitsPerChannel
      );

      const bitOffset = bitIndex % bitsPerChannel;

      if (channelOffset < 3) {
        const bit = (imageData[baseIndex + channelOffset] >> bitOffset) & 1;
        byte |= bit << j;
      }

      bitIndex++;
    }

    extractedData[i] = byte;
  }

  const result = header.isEncrypted
    ? vigenereProcess(extractedData, key, false)
    : extractedData;

  return result;
}

export function hideDataBPCS(
  imageData: Uint8ClampedArray,
  fileData: Uint8Array,
  key: string,
  threshold: number = 0.4,
  metadata: EncryptionMetadata
): Uint8ClampedArray {
  if (key.length > 25) {
    throw new Error("Stego-key must be exactly 25 characters long");
  }

  // Prepare seed from key
  const seed = createSeedFromKey(key);

  // Create a copy of the image data
  const modifiedImageData = new Uint8ClampedArray(imageData);

  const fileDataToHide = metadata.encrypted
    ? vigenereProcess(fileData, key, true)
    : fileData;

  // Create header containing file size and metadata
  const fileSize = fileDataToHide.length;
  const header = createHeader(
    fileSize,
    "BPCS",
    threshold,
    metadata.encrypted,
    metadata.name
  );

  console.log(header);

  // Combine header and file data
  const dataToHide = new Uint8Array(HEADER_SIZE + fileDataToHide.length);
  dataToHide.set(header, 0);
  dataToHide.set(fileDataToHide, HEADER_SIZE);

  // Convert image to bit planes
  const width = Math.sqrt(imageData.length / 4); // Estimate width from RGBA data
  const height = width;
  const bitPlanes = extractBitPlanes(modifiedImageData, width, height);

  // Find complex regions in bit planes
  const complexRegions = findComplexRegions(bitPlanes, threshold);

  // Check if we have enough complex regions
  const dataBytes = dataToHide.length;
  const dataBits = dataBytes * 8;
  const bitsPerRegion = 8 * 8; // 8x8 block
  const regionsNeeded = Math.ceil(dataBits / bitsPerRegion);

  if (regionsNeeded > complexRegions.length) {
    throw new Error(
      `File too large to hide using BPCS. Need ${regionsNeeded} regions, but only ${complexRegions.length} available.`
    );
  }

  // Convert data to embed into bit blocks
  const dataBlocks = convertDataToBlocks(dataToHide);

  // Use the key to shuffle complex regions
  const shuffledRegions = shuffleComplexRegions(complexRegions, seed);

  // Embed data blocks into complex regions
  for (let i = 0; i < dataBlocks.length; i++) {
    if (i >= shuffledRegions.length) break;

    const regionInfo = shuffledRegions[i];
    embedBlockInBitPlane(
      bitPlanes[regionInfo.plane],
      dataBlocks[i],
      regionInfo.x,
      regionInfo.y
    );
  }

  // Convert bit planes back to image data
  mergeBitPlanesToImage(bitPlanes, modifiedImageData, width, height);

  return modifiedImageData;
}

export function extractDataBPCS(
  imageData: Uint8ClampedArray,
  key: string,
  parsedHeader: Header,
  seed: number
): Uint8Array {
  // Convert image to bit planes
  console.log(parsedHeader);
  const width = Math.sqrt(imageData.length / 4); // Estimate width from RGBA data
  const height = width;
  const bitPlanes = extractBitPlanes(imageData, width, height);

  // Use the already parsed header
  const fileSize = parsedHeader.fileSize;
  const threshold = parsedHeader.threshold ?? 0.4;
  const encrypted = parsedHeader.isEncrypted || false;

  // Find complex regions using the threshold from header
  const complexRegions = findComplexRegions(bitPlanes, threshold);

  // Use key to get same shuffled order as embedding
  const shuffledRegions = shuffleComplexRegions(complexRegions, seed);

  // Calculate how many regions needed for file (header is already extracted)
  const fileBits = fileSize * 8;
  const bitsPerRegion = 8 * 8;
  const regionsForFile = Math.ceil(fileBits / bitsPerRegion);

  console.log(shuffledRegions.length);
  console.log(regionsForFile);
  console.log(fileBits);

  if (shuffledRegions.length < regionsForFile) {
    throw new Error("File data appears to be corrupted or incomplete.");
  }

  // Calculate the starting region (skip header regions)
  const headerBits = HEADER_SIZE * 8;
  const regionsForHeader = Math.ceil(headerBits / bitsPerRegion);

  // Extract file data blocks (skipping header blocks)
  const fileBlocks: boolean[][] = [];
  for (let i = regionsForHeader; i < regionsForHeader + regionsForFile; i++) {
    if (i >= shuffledRegions.length) break;

    const region = shuffledRegions[i];
    const block = extractBlockFromBitPlane(
      bitPlanes[region.plane],
      region.x,
      region.y
    );
    fileBlocks.push(block);
  }

  // Convert blocks to data bytes
  const fileData = convertBlocksToData(fileBlocks, fileSize);

  // Decrypt data if it was encrypted with Vigenère
  if (encrypted) {
    return vigenereProcess(fileData, key, false); // Decrypt
  }

  return fileData;
}

export function calculatePSNR(
  originalImageData: Uint8ClampedArray,
  stegoImageData: Uint8ClampedArray
): number {
  if (originalImageData.length !== stegoImageData.length) {
    throw new Error("Image dimensions don't match");
  }

  // Calculate Mean Squared Error (MSE)
  let sumSquaredDiff = 0;
  for (let i = 0; i < originalImageData.length; i++) {
    const diff = originalImageData[i] - stegoImageData[i];
    sumSquaredDiff += diff * diff;
  }

  const mse = sumSquaredDiff / originalImageData.length;

  // If images are identical, PSNR is infinity
  if (mse === 0) return Infinity;

  // Calculate PSNR (max pixel value for 8-bit image is 255)
  const maxPixelValue = 255;
  const psnr = 10 * Math.log10((maxPixelValue * maxPixelValue) / mse);

  return psnr;
}

function createSeedFromKey(key: string): number {
  let seed = 0;
  for (let i = 0; i < key.length; i++) {
    seed = (seed << 5) - seed + key.charCodeAt(i);
    seed = seed & seed; // Convert to 32-bit integer
  }
  return Math.abs(seed);
}

function generatePixelIndices(
  seed: number,
  maxPixels: number,
  totalBitsNeeded: number
): number[] {
  // Create a pseudo-random number generator
  const rng = mulberry32(seed);

  // Calculate how many pixels we need
  const pixelsNeeded = Math.ceil(totalBitsNeeded / 3); // 3 color channels per pixel

  // Create array of all possible indices
  const allIndices = Array.from({ length: maxPixels }, (_, i) => i);

  // Shuffle array using Fisher-Yates algorithm with our seeded RNG
  for (let i = allIndices.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [allIndices[i], allIndices[j]] = [allIndices[j], allIndices[i]];
  }

  // Return only the number of indices we need
  return allIndices.slice(0, pixelsNeeded);
}

/**
 * Simple seeded random number generator (Mulberry32)
 */
function mulberry32(a: number): () => number {
  return function () {
    let t = (a += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function isHeaderValid(header: Uint8Array) {
  return header[8] === CONSTANT;
}

/**
 * Create a header with file metadata
 */
function createHeader(
  fileSize: number,
  method: "LSB" | "BPCS",
  parameter: number,
  isEncrypted: boolean,
  filename: string
): Uint8Array {
  const header = new Uint8Array(HEADER_SIZE);

  // First 4 bytes: File size
  header[0] = (fileSize >> 24) & 0xff;
  header[1] = (fileSize >> 16) & 0xff;
  header[2] = (fileSize >> 8) & 0xff;
  header[3] = fileSize & 0xff;

  // Next byte: Method (0 for LSB, 1 for BPCS)
  header[4] = method === "LSB" ? 0 : 1;

  // Next byte: Parameter (bits per channel for LSB, threshold * 100 for BPCS)
  console.log(parameter);
  header[5] = method === "LSB" ? parameter : Math.floor(parameter * 100);
  console.log(header[5]);

  header[6] = isEncrypted ? 1 : 0;

  // Next byte: Filename length
  // Since we have 32 - 7 = 25 bytes left for the filename, limit to 25 characters
  const maxFilenameLength = HEADER_SIZE - 8;
  const truncatedFilename = filename.slice(0, maxFilenameLength);
  header[7] = truncatedFilename.length;

  // Next bytes: Filename (ASCII encoded for simplicity)
  for (let i = 0; i < truncatedFilename.length && i < maxFilenameLength; i++) {
    header[8 + i] = truncatedFilename.charCodeAt(i);
  }

  return header;
}

/**
 * Parse header to extract file metadata
 */
function parseHeader(header: Uint8Array): Header {
  // Extract file size from first 4 bytes
  console.log(header);
  const fileSize =
    (header[0] << 24) | (header[1] << 16) | (header[2] << 8) | header[3];

  // Extract method
  const methodCode = header[4];
  const method = methodCode === 0 ? "LSB" : "BPCS";

  // Extract parameter
  console.log(header[5]);
  const parameter = method === "LSB" ? header[5] : header[5] / 100;

  // Extract filename length
  const isEncrypted = header[6] === 1;

  // Extract filename length
  const filenameLength = header[7];

  // Extract filename
  let filename = "";
  for (let i = 0; i < filenameLength && i < HEADER_SIZE - 8; i++) {
    filename += String.fromCharCode(header[8 + i]);
  }

  if (method === "LSB") {
    return {
      fileSize,
      method,
      bitsPerChannel: parameter,
      isEncrypted,
      filename,
    };
  } else {
    return {
      fileSize,
      method,
      threshold: parameter,
      isEncrypted,
      filename,
    };
  }
}

/**
 * Extract bit planes from image data
 */
function extractBitPlanes(
  imageData: Uint8ClampedArray,
  width: number,
  height: number
): boolean[][][] {
  // Initialize bit planes (8 bit planes x 3 channels - RGB)
  const bitPlanes: boolean[][][] = Array(24)
    .fill(0)
    .map(() =>
      Array(height)
        .fill(0)
        .map(() => Array(width).fill(false))
    );

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const pixelIndex = (y * width + x) * 4; // RGBA

      // Process each channel (RGB)
      for (let channel = 0; channel < 3; channel++) {
        const value = imageData[pixelIndex + channel];

        // Extract each bit
        for (let bit = 0; bit < 8; bit++) {
          const planeIndex = channel * 8 + bit;
          bitPlanes[planeIndex][y][x] = ((value >> bit) & 1) === 1;
        }
      }
    }
  }

  return bitPlanes;
}

/**
 * Find complex regions in bit planes
 */
function findComplexRegions(
  bitPlanes: boolean[][][],
  threshold: number
): Array<{ plane: number; x: number; y: number; complexity: number }> {
  const complexRegions: Array<{
    plane: number;
    x: number;
    y: number;
    complexity: number;
  }> = [];

  // For each bit plane
  for (let plane = 0; plane < bitPlanes.length; plane++) {
    const planeData = bitPlanes[plane];
    const height = planeData.length;
    const width = planeData[0].length;

    // Skip processing of the most significant bit planes (0-1) for better visual quality
    if (plane % 8 < 2) continue;

    // Divide into 8x8 blocks
    for (let blockY = 0; blockY <= height - 8; blockY += 8) {
      for (let blockX = 0; blockX <= width - 8; blockX += 8) {
        // Calculate complexity of this block
        const complexity = calculateBlockComplexity(planeData, blockX, blockY);

        // If complexity exceeds threshold, add to complex regions
        if (complexity >= threshold) {
          complexRegions.push({
            plane,
            x: blockX,
            y: blockY,
            complexity,
          });
        }
      }
    }
  }

  return complexRegions;
}

/**
 * Calculate complexity of an 8x8 block
 */
function calculateBlockComplexity(
  plane: boolean[][],
  startX: number,
  startY: number
): number {
  let changes = 0;
  const maxChanges = 2 * 8 * 7; // Maximum possible changes in an 8x8 block

  // Check horizontal changes
  for (let y = 0; y < 8; y++) {
    for (let x = 0; x < 7; x++) {
      if (plane[startY + y][startX + x] !== plane[startY + y][startX + x + 1]) {
        changes++;
      }
    }
  }

  // Check vertical changes
  for (let x = 0; x < 8; x++) {
    for (let y = 0; y < 7; y++) {
      if (plane[startY + y][startX + x] !== plane[startY + y + 1][startX + x]) {
        changes++;
      }
    }
  }

  return changes / maxChanges;
}

/**
 * Convert data bytes to 8x8 boolean blocks
 */
function convertDataToBlocks(data: Uint8Array): boolean[][] {
  const blocks: boolean[][] = [];
  let currentBlock: boolean[] = [];

  for (let i = 0; i < data.length; i++) {
    const byte = data[i];

    // Convert byte to bits
    for (let bit = 7; bit >= 0; bit--) {
      currentBlock.push(((byte >> bit) & 1) === 1);

      if (currentBlock.length === 64) {
        // 8x8 block
        blocks.push([...currentBlock]);
        currentBlock = [];
      }
    }
  }

  // Pad last block if needed
  if (currentBlock.length > 0) {
    while (currentBlock.length < 64) {
      currentBlock.push(false);
    }
    blocks.push(currentBlock);
  }

  return blocks;
}

/**
 * Shuffle complex regions using key-derived seed
 */
function shuffleComplexRegions(
  regions: Array<{ plane: number; x: number; y: number; complexity: number }>,
  seed: number
): Array<{ plane: number; x: number; y: number; complexity: number }> {
  const shuffled = [...regions];
  const rng = mulberry32(seed);

  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }

  return shuffled;
}

/**
 * Embed an 8x8 data block into a bit plane
 */
function embedBlockInBitPlane(
  plane: boolean[][],
  block: boolean[],
  startX: number,
  startY: number
): void {
  for (let y = 0; y < 8; y++) {
    for (let x = 0; x < 8; x++) {
      const index = y * 8 + x;
      if (index < block.length) {
        plane[startY + y][startX + x] = block[index];
      }
    }
  }
}

/**
 * Extract an 8x8 data block from a bit plane
 */
function extractBlockFromBitPlane(
  plane: boolean[][],
  startX: number,
  startY: number
): boolean[] {
  const block: boolean[] = [];

  for (let y = 0; y < 8; y++) {
    for (let x = 0; x < 8; x++) {
      block.push(plane[startY + y][startX + x]);
    }
  }

  return block;
}

/**
 * Convert extracted boolean blocks back to data bytes
 */
function convertBlocksToData(blocks: boolean[][], length: number): Uint8Array {
  const result = new Uint8Array(length);
  let resultIndex = 0;
  let bitCount = 0;
  let currentByte = 0;

  // Process all blocks
  for (const block of blocks) {
    for (const bit of block) {
      // Add bit to current byte
      currentByte = (currentByte << 1) | (bit ? 1 : 0);
      bitCount++;

      // If we have a complete byte
      if (bitCount === 8) {
        if (resultIndex < length) {
          result[resultIndex] = currentByte;
          resultIndex++;
        }
        bitCount = 0;
        currentByte = 0;
      }

      // Stop if we've filled the result
      if (resultIndex >= length) break;
    }

    if (resultIndex >= length) break;
  }

  return result;
}

/**
 * Merge bit planes back into image data
 */
function mergeBitPlanesToImage(
  bitPlanes: boolean[][][],
  imageData: Uint8ClampedArray,
  width: number,
  height: number
): void {
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const pixelIndex = (y * width + x) * 4; // RGBA

      // For each channel (RGB)
      for (let channel = 0; channel < 3; channel++) {
        let value = 0;

        // Reconstruct byte from bit planes
        for (let bit = 0; bit < 8; bit++) {
          const planeIndex = channel * 8 + bit;
          if (bitPlanes[planeIndex][y][x]) {
            value |= 1 << bit;
          }
        }

        imageData[pixelIndex + channel] = value;
      }

      // Keep alpha channel unchanged
      // imageData[pixelIndex + 3] remains the same
    }
  }
}
