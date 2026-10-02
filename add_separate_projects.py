import os
import shutil
from app import app, db
from models import Project, Category, ProjectImage, slugify

projects_data = [
    {
        'title': 'Sparsh Hospital Lobby',
        'image': 'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273021.jpg'
    },
    {
        'title': 'Aditya Birla UltraTech',
        'image': 'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273027.jpg'
    },
    {
        'title': 'Banquet Hall',
        'image': 'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273034.jpg'
    },
    {
        'title': 'Sparsh Hospital Exterior',
        'image': 'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273057.jpg'
    },
    {
        'title': 'A.M. Naik Immersive Showcase',
        'image': 'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940273087.jpg'
    }
]

with app.app_context():
    category = Category.query.first()
    cat_id = category.id if category else None
    
    for idx, p_data in enumerate(projects_data):
        project = Project(
            title=p_data['title'],
            slug=slugify(p_data['title']),
            description=f"Project details for {p_data['title']}",
            is_featured=True,
            category_id=cat_id,
            status='published'
        )
        db.session.add(project)
        db.session.flush() # get id
        
        filename = f"featured_proj_{idx}_{os.path.basename(p_data['image'])}"
        dest_path = os.path.join('static', 'uploads', filename)
        shutil.copy(p_data['image'], dest_path)
        
        pi = ProjectImage(
            project_id=project.id,
            filename=filename,
            is_cover=True,
            sort_order=0
        )
        db.session.add(pi)
        
    db.session.commit()
    print("Added 5 separate projects.")
