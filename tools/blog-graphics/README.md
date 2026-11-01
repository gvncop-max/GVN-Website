# Blog graphics

Branded charts and graphics for P-Pulse posts (navy / cream / gold, the site's
own fonts). Each is an HTML page screenshotted by headless Chrome.

- Bar chart: write a JSON file like `rents.json`, then
  `python barchart.py rents.json rents.html`
- Free-form graphic: copy `timeline.html` or `checklist.html` (they use
  `base.css`).
- Render the landscape version (body images, 1200x800) and the phone version
  (portrait, rendered at 600 wide, saved at 2x):
  `python render.py rents.html <slug>-2.webp 1200 800`
  `python render.py rents.html <slug>-2-m.webp 600 940 2`
- In the post, wrap the image so phones get the portrait one:
  `<picture><source media="(max-width: 640px)" srcset="...-2-m.webp" width="1200" height="1880"><img src="...-2.webp" ...></picture>`
- Print the source on every chart, and only plot verified figures.

Needs Google Chrome at the default path and Pillow.
