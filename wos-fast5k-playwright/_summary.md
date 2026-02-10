Automating bulk exports from Web of Science, this experiment introduces a Playwright script that segments large result sets into precise 5,000-record batches for Fast 5K downloads, automatically handling the final batch size. The workflow requires the user to log in and conduct a search manually, after which the script reads the total record count, computes exact ranges, fills the export dialog, and sequentially saves batches with customizable file naming. Selector handling is robust but adaptable, providing reliability across varying Web of Science interfaces. The tool can be accessed via the provided [GitHub repository](https://github.com/your-repo/download_wos_fast5k) for deployment, with basic setup via Node.js and Playwright.

**Key Features and Findings:**
- Ensures accurate export batches, preventing over/under-collection in the final batch.
- Supports sequential file naming and customizable batch size.
- Efficient for exporting thousands of records from Web of Science without manual range entry.
- Selector tweaks may be required based on platform UI differences.

For more details on Playwright automation, see [Playwright documentation](https://playwright.dev/).
