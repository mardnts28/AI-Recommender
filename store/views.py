from django.shortcuts import render, redirect
from django.conf import settings
from .models import Product
from .forms import ProductForm
from .mongo import products_collection
from google import genai

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_tags(product_name, description=""):
    """Only called when ADDING a product — not on every search."""
    prompt = f"""
    Generate 4-6 short product tags for this item.
    Product: {product_name}
    Description: {description}

    Return ONLY a comma-separated list of lowercase tags.
    Example: electronics, wireless, portable, budget-friendly
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip()
        return [tag.strip() for tag in raw.split(",") if tag.strip()]
    except Exception:
        # Fallback if quota exceeded
        words = (product_name + " " + description).lower().split()
        return list(dict.fromkeys(words))[:5]


def get_recommendations(query, products):
    """Smart keyword matching — no API needed."""
    if not query or not products:
        return []

    query_words = [w.lower().strip() for w in query.split() if w.strip()]

    scored = []
    for product in products:
        product_tags = [t.lower() for t in (product.tags or [])]
        product_name_words = product.name.lower().split()
        all_product_words = product_tags + product_name_words

        score = 0
        for qw in query_words:
            for pw in all_product_words:
                if qw in pw or pw in qw:
                    score += 1

        if score > 0:
            scored.append({'product': product, 'score': score})

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored


def home(request):
    query = request.GET.get('q', '').strip()
    recommendations = []

    if query:
        products = Product.objects.all()
        recommendations = get_recommendations(query, products)

    return render(request, 'store/home.html', {
        'query': query,
        'recommendations': recommendations,
    })


def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)

            tags_input = form.cleaned_data.get('tags_input', '')
            manual_tags = [t.strip().lower() for t in tags_input.split(',') if t.strip()]
            ai_tags = generate_tags(product.name, product.description)

            all_tags = list(dict.fromkeys(manual_tags + ai_tags))
            product.tags = all_tags
            product.save()

            products_collection.insert_one({
                'name': product.name,
                'price': float(product.price),
                'description': product.description,
                'tags': product.tags,
            })

            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'store/add_product.html', {'form': form})