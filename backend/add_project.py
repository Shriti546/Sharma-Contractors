import os
import shutil
from app import app, db
from models import Project, Category, ProjectImage, slugify

with app.app_context():
    # Ensure static/uploads exists
    os.makedirs('static/uploads', exist_ok=True)
    
    # Create the project
    category = Category.query.first() # Get a category, any category
    cat_id = category.id if category else None
    
    project = Project(
        title='Sparsh Hospital',
        slug=slugify('Sparsh Hospital'),
        description='A new hospital construction and interior project.',
        is_featured=True,
        category_id=cat_id,
        status='published'
    )
    db.session.add(project)
    db.session.commit()
    
    images = [
        'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273021.jpg',
        'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273027.jpg',
        'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273034.jpg',
        'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273057.jpg',
        'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273087.jpg'
    ]
    
    for i, img_path in enumerate(images):
        filename = f'project_1_{i}.jpg'
        dest_path = os.path.join('static', 'uploads', filename)
        shutil.copy(img_path, dest_path)
        
        pi = ProjectImage(
            project_id=project.id,
            filename=filename,
            is_cover=(i == 0),
            sort_order=i
        )
        db.session.add(pi)
        
    db.session.commit()
    print('Project and images added successfully.')
