# DevH Admin and Blog System

A comprehensive admin and blog management system with role-based access control.

## Features

- Universal admin system with role-based access control
- Blog management system
- Secure password-based authentication
- RESTful API endpoints for both admin and blog operations

## Database Collections

- `devh_admins`: Stores admin user information
- `devh_blog`: Stores blog posts

## Initial Setup

The system comes with a pre-configured super admin:
- Email: ***@devh.in
- Password: ***

## API Endpoints

### Admin Routes

- GET `/admin/<admin_id>`: Get admin details
- GET `/admins`: List all admins
- POST `/admin`: Create new admin (super admin only)
- PUT `/admin/<admin_id>`: Update admin details
- DELETE `/admin/<admin_id>`: Delete admin (super admin only)

### Blog Routes

- GET `/blog/<blog_id>`: Get blog details
- GET `/blogs`: List all blogs
- GET `/admin/<admin_id>/blogs`: List admin's blogs
- POST `/blog`: Create new blog
- PUT `/blog/<blog_id>`: Update blog
- DELETE `/blog/<blog_id>`: Delete blog

## Authentication

The system uses Basic Authentication. Include your email and password in the Authorization header for protected routes.
