import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = ({ isAuthenticated, user, logout }) => {
    return (
        <nav className="navbar">
            <Link to="/">E-commerce Chatbot</Link>
            {isAuthenticated ? (
                <div className="nav-links">
                    <span>Welcome, {user.username}</span>
                    <button onClick={logout}>Logout</button>
                </div>
            ) : (
                <div className="nav-links">
                    <Link to="/login">Login</Link>
                    <Link to="/register">Register</Link>
                </div>
            )}
        </nav>
    );
};

export default Navbar;
