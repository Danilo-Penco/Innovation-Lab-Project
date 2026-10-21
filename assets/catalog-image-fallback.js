(() => {
  const showFallback = (image) => {
    if (
      !(image instanceof HTMLImageElement) ||
      !image.id.startsWith("catalog-cover-")
    ) {
      return;
    }

    image.style.display = "none";
    const fallbackId = image.id.replace("catalog-cover-", "catalog-fallback-");
    const fallback = document.getElementById(fallbackId);
    if (fallback) {
      fallback.style.display = "flex";
    }
  };

  document
    .querySelectorAll('img[id^="catalog-cover-"]')
    .forEach((image) => {
      if (image.complete && image.naturalWidth === 0) {
        showFallback(image);
      }
    });

  document.addEventListener("error", (event) => showFallback(event.target), true);
})();
