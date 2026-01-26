import JSZip from "jszip";

export type DownloadablePanelData = {
  index: number;
  imageUrl: string;
};

export const downloadPanelsZip = async (
  downloadablePanels: DownloadablePanelData[]
): Promise<void> => {
  console.log("downloading panels", downloadablePanels);
  const zip = new JSZip();

  // Fetch all images in parallel
  const fetchImages = downloadablePanels.map(
    async ({ index, imageUrl }) => {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const contentType = response.headers.get("content-type");
      const extension = contentType?.includes("jpeg")
        ? ".jpeg"
        : ".png";
      return { filename: `panel-${index + 1}.${extension}`, blob };
    }
  );
  const files = await Promise.all(fetchImages);

  // Add each image to zip
  for (const { filename, blob } of files) {
    zip.file(filename, blob);
  }

  // Download zip
  const zipBlob = await zip.generateAsync({ type: "blob" });

  // Trigger download
  const url = URL.createObjectURL(zipBlob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `comic-panels-${Date.now()}.zip`;
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
