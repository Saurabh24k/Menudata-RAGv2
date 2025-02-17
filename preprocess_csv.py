import pandas as pd
import re
import os

# Define file paths
input_file = "data/cleaned_menu_wiki_augmented.csv"  # Update with actual path if needed
output_file = "data/cleaned_menu.csv"

# Load the CSV file
df = pd.read_csv(input_file)

### 1️⃣ Handle Missing Values
# Fill missing descriptions with "No description available"
df['menu_description'].fillna("No description available", inplace=True)

# Fill missing ingredient names with "Unknown ingredients"
df['ingredient_name'].fillna("Unknown ingredients", inplace=True)

# Drop rows where essential fields are missing (restaurant_name, menu_item, address)
df.dropna(subset=['restaurant_name', 'menu_item', 'address1'], inplace=True)

### 2️⃣ Normalize Text
def clean_text(text):
    """Lowercase, remove special characters, and trim spaces."""
    if isinstance(text, str):
        text = text.lower().strip()  # Convert to lowercase & strip spaces
        text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
    return text

# Apply text cleaning
text_columns = ['restaurant_name', 'menu_category', 'menu_item', 'menu_description', 'ingredient_name', 'city', 'state', 'country']
for col in text_columns:
    df[col] = df[col].astype(str).apply(clean_text)

### 3️⃣ Filter Out Low-Confidence Entries
confidence_threshold = 0.7  # Adjust if needed
df = df[df['confidence'] >= confidence_threshold]

### 4️⃣ Create a Concatenated Text Column for Better Embeddings
df['combined_text'] = (
    "Restaurant: " + df['restaurant_name'] + " | "
    "Category: " + df['menu_category'] + " | "
    "Item: " + df['menu_item'] + " | "
    "Description: " + df['menu_description'] + " | "
    "Ingredients: " + df['ingredient_name'] + " | "
    "Location: " + df['city'] + ", " + df['state'] + " | "
    "Rating: " + df['rating'].astype(str) + " | "
    "Reviews: " + df['review_count'].astype(str) + " | "
    "Price: " + df['price'].astype(str)
)

### 5️⃣ Save the Cleaned CSV
df.to_csv(output_file, index=False)

print(f"✅ Preprocessing complete! Cleaned data saved as: {output_file}")
