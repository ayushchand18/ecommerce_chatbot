import React from 'react';

const ProductCard = ({ product }) => {
  return (
    <div className="product-card">
      <div className="product-image">
        <img src={product.image_url || 'https://via.placeholder.com/150'} alt={product.name} />
      </div>
      <div className="product-details">
        <h4>{product.name}</h4>
        <p className="product-price">${product.price.toFixed(2)}</p>
        <p className="product-category">{product.category}</p>
        <p className="product-description">{product.description.substring(0, 60)}...</p>
        <button className="add-to-cart">Add to Cart</button>
      </div>
    </div>
  );
};

export default ProductCard;