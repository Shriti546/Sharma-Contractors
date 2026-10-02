import os
import shutil
from app import app, db
from models import Project, Category, ProjectImage, slugify

with app.app_context():
    category = Category.query.first()
    cat_id = category.id if category else None
    
    title = 'Modern Office Workspace'
    img_path = 'C:/Users/Shriti/.gemini/antigravity/brain/e9241945-1063-4d21-8b10-bdb762068c7f/.user_uploaded/media_1790940687909.jpg'
    
    project = Project(
        title=title,
        slug=slugify(title),
        description=f"Project details for {title}",
        is_featured=True,
        category_id=cat_id,
        status='published'
    )
    db.session.add(project)
    db.session.flush()
    
    filename = f"featured_proj_5_{os.path.basename(img_path)}"
    dest_path = os.path.join('static', 'uploads', filename)
    shutil.copy(img_path, dest_path)
    
    pi = ProjectImage(
        project_id=project.id,
        filename=filename,
        is_cover=True,
        sort_order=0
    )
    db.session.add(pi)
    
    db.session.commit()
    print("Added new office project.")
