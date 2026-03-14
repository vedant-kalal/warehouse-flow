from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models import Product, Category
from config import settings


def build_embed_text(product: Product, category_name: str | None = None) -> str:
    """Build rich text for embedding from product data."""
    text = f"Product: {product.name}\nCategory: {category_name or 'Unknown'}\nSKU: {product.sku}\nUnit: {product.unit}"
    return text


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector from text using Sentence Transformer (free, local model)."""
    try:
        from sentence_transformers import SentenceTransformer

        # Load Sentence Transformer model (384-dimensional embeddings)
        # 'all-MiniLM-L6-v2' is lightweight, fast, and high quality
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Generate embedding
        embedding = model.encode(text, convert_to_tensor=False)

        # Convert numpy array to list
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return dummy embedding on error (384 dims for all-MiniLM-L6-v2)
        return [0.0] * 384


async def generate_and_store(db: AsyncSession, product: Product) -> None:
    """Generate embedding and store in product."""
    # Fetch category name
    result = await db.execute(
        select(Category).where(Category.id == product.category_id)
    )
    category = result.scalar_one_or_none()
    category_name = category.name if category else "Unknown"

    # Build text and generate embedding
    embed_text = build_embed_text(product, category_name)
    embedding = await generate_embedding(embed_text)

    # Store in product
    product.embedding = embedding
    await db.commit()


async def bulk_embed_products(db: AsyncSession) -> int:
    """Bulk embed all products that don't have embeddings."""
    # Fetch all products without embeddings
    result = await db.execute(
        select(Product)
        .where(Product.embedding.is_(None))
        .options(joinedload(Product.category))
    )
    products = result.unique().scalars().all()

    # Process in batches of 100
    batch_size = 100
    for i in range(0, len(products), batch_size):
        batch = products[i:i+batch_size]

        for product in batch:
            try:
                await generate_and_store(db, product)
            except Exception as e:
                print(f"Error embedding product {product.id}: {e}")

    return len(products)
