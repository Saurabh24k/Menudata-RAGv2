import pandas as pd
import wikipediaapi
import threading
from tqdm import tqdm  # For progress tracking

# Dictionary to cache Wikipedia results (avoid redundant requests)
wiki_cache = {}

def fetch_wikipedia_summary(term):
    """Fetch Wikipedia summary for a given term, using caching."""
    if term in wiki_cache:
        return wiki_cache[term]  # ✅ Return cached result if available
    
    USER_AGENT = "MyDatasetAugmenter/1.0 (contact: saurabhrajput24k@gmail.com)"
    wiki_wiki = wikipediaapi.Wikipedia(language="en", user_agent=USER_AGENT)

    page = wiki_wiki.page(term)
    if page.exists():
        summary = page.summary[:500]  # Limit to first 500 characters
    else:
        summary = "No Wikipedia data available"

    wiki_cache[term] = summary  # ✅ Store result in cache
    return summary

def augment_with_wikipedia(file_path):
    """Augment the cleaned menu CSV with Wikipedia data for multiple columns (faster with caching + threading)."""
    df = pd.read_csv(file_path)

    # Columns to augment with Wikipedia
    wiki_columns = ["menu_category", "menu_item", "ingredient_name", "categories", "city", "country", "state"]
    
    print("\n🔍 Fetching Wikipedia data for:", wiki_columns)
    tqdm.pandas()  # Enable progress tracking

    for col in wiki_columns:
        if col in df.columns:
            print(f"\n🌍 Augmenting `{col}` with Wikipedia summaries...")
            
            # ✅ Use threading to speed up Wikipedia requests
            def fetch_parallel(index, value):
                df.at[index, f"{col}_wiki_summary"] = fetch_wikipedia_summary(value)

            threads = []
            for index, value in tqdm(df[col].items(), total=len(df[col]), desc=f"🔄 Fetching {col}"):
                thread = threading.Thread(target=fetch_parallel, args=(index, value))
                threads.append(thread)
                thread.start()

                if len(threads) >= 10:  # ✅ Control concurrency to avoid API rate limits
                    for t in threads:
                        t.join()
                    threads = []

            # Ensure remaining threads finish
            for t in threads:
                t.join()

    # Save new CSV with Wikipedia data
    output_path = file_path.replace(".csv", "_wiki_augmented.csv")
    df.to_csv(output_path, index=False)

    print(f"\n✅ Wikipedia data successfully added! Saved as `{output_path}`")
    return df

# Run the augmentation on your cleaned menu CSV
csv_path = "data/cleaned_menu.csv"
df_augmented = augment_with_wikipedia(csv_path)
