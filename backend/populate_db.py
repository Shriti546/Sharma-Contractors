import os
import re
import shutil
from collections import defaultdict
from app import app, db
from models import Project, Category, ProjectImage, slugify

images_dir = 'images'
upload_dir = os.path.join('static', 'uploads')
os.makedirs(upload_dir, exist_ok=True)
files = os.listdir(images_dir)

pattern = re.compile(r'^(.*?)\s*\(\s*(\d+)\s*\)\.[a-zA-Z0-9]+$')
projects = defaultdict(list)

for f in files:
    match = pattern.match(f)
    if match:
        proj_name = match.group(1).strip()
        key = proj_name.lower()
        projects[key].append((int(match.group(2)), f, proj_name))

with app.app_context():
    category = Category.query.first()
    cat_id = category.id if category else None

    # Delete existing projects that might conflict, or just delete all projects? 
    # Let's keep the ones we added earlier, but if it has the same name we skip or overwrite.
    for key, items in projects.items():
        items.sort(key=lambda x: x[0])
        proj_display_name = items[0][2]
        
        # Check if project already exists
        existing = Project.query.filter_by(title=proj_display_name).first()
        if existing:
            db.session.delete(existing)
            db.session.flush()

        project = Project(
            title=proj_display_name,
            slug=slugify(proj_display_name),
            description=f"Project details for {proj_display_name}",
            is_featured=False, # Wait, the user didn't ask to feature them. I'll just set False, or maybe True.
            category_id=cat_id,
            status='published'
        )
        db.session.add(project)
        db.session.flush()

        for idx, (num, filename, _) in enumerate(items):
            src_path = os.path.join(images_dir, filename)
            dest_path = os.path.join(upload_dir, filename)
            
            # Copy to static/uploads to ensure Flask serves it properly
            # and it's managed like other uploads. We don't delete original.
            if not os.path.exists(dest_path):
                shutil.copy(src_path, dest_path)
            
            is_cover = (num == 1)
            pi = ProjectImage(
                project_id=project.id,
                filename=filename,
                is_cover=is_cover,
                sort_order=num
            )
            db.session.add(pi)
            
    db.session.commit()
    print("Database populated successfully.")
