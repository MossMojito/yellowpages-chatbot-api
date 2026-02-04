# YellowPages Scraper (Episode 1) 🕷️

This module contains the logic for scraping business data from **YellowPages Thailand**.
It uses a hybrid approach with **Crawl4AI** (for browser handling) and **BeautifulSoup** (for efficient parsing).

## 📂 Structure

-   `main.py`: The executable scraper script.
-   `requirements.txt`: Dependencies for the scraper.
-   `*.ipynb`: Original research notebooks (archived).

## 🚀 How to Run

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Scraper**:
    ```bash
    python main.py --category "กีฬา"
    ```
    (You can change "กีฬา" to any other category keyword).

3.  **Output**:
    -   The script will generate a CSV file (e.g., `yellowpages_กีฬา.csv`) with the extracted data.
    -   You can move this file to `../data/raw/` to be processed by the Chatbot AI.
