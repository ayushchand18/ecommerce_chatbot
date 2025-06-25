from faker import Faker
from random import randint, choice
from app import app, db, Product

fake = Faker()

categories = [
    'Electronics',
    'Books',
    'Clothing',
    'Home & Kitchen',
    'Sports & Outdoors',
    'Toys & Games'
]

electronics = [
    'Laptop', 'Smartphone', 'Headphones', 'Smartwatch', 'Tablet',
    'Camera', 'Speaker', 'Monitor', 'Keyboard', 'Mouse'
]

books = [
    'Novel', 'Textbook', 'Biography', 'Cookbook', 'Fantasy',
    'Science Fiction', 'Mystery', 'Romance', 'History', 'Self-Help'
]

clothing = [
    'T-Shirt', 'Jeans', 'Dress', 'Jacket', 'Sweater',
    'Shorts', 'Skirt', 'Coat', 'Socks', 'Underwear'
]

def generate_product_name(category):
    if category == 'Electronics':
        return f"{choice(electronics)} {fake.word().capitalize()}"
    elif category == 'Books':
        return f"{fake.sentence(nb_words=3)}"
    elif category == 'Clothing':
        return f"{choice(clothing)} {fake.color_name()}"
    else:
        return fake.catch_phrase()

def create_mock_products(count=100):
    with app.app_context():
        Product.query.delete()  # Clear existing products
        
        for _ in range(count):
            category = choice(categories)
            name = generate_product_name(category)
            product = Product(
                name=name,
                description=fake.paragraph(nb_sentences=3),
                price=round(randint(10, 1000) + randint(0, 99)/100,
                category=category,
                stock=randint(0, 100),
                image_url=f'https://picsum.photos/300/200?random={randint(1, 1000)}'
            )
            db.session.add(product)
        
        db.session.commit()
        print(f"Created {count} mock products")

if __name__ == '__main__':
    create_mock_products()