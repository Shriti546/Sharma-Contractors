
content = open('app.py', 'r', encoding='utf-8').read()

NEW_SYNC_BLOCK = '''
import shutil
from collections import defaultdict

LAST_SYNC_TIME = 0

def sync_images_folder():
    global LAST_SYNC_TIME
    images_dir = 'images'
    upload_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(images_dir):
        return

    try:
        current_mtime = os.path.getmtime(images_dir)
    except Exception:
        return

    if current_mtime <= LAST_SYNC_TIME:
        return

    LAST_SYNC_TIME = current_mtime

    files = os.listdir(images_dir)
    img_pattern = re.compile(r\'^(.*?)\\s*\\(\\s*(\\d+)\\s*\\)\\.[a-zA-Z0-9]+$\')
    projects_dict = defaultdict(list)

    for f in files:
        match = img_pattern.match(f)
        if match:
            proj_name = match.group(1).strip()
            key = proj_name.lower()
            projects_dict[key].append((int(match.group(2)), f, proj_name))

    if not projects_dict:
        return

    category = Category.query.first()
    cat_id = category.id if category else None

    for key, items in projects_dict.items():
        items.sort(key=lambda x: x[0])
        proj_display_name = items[0][2]
        slug = slugify(proj_display_name)

        project = Project.query.filter_by(slug=slug).first()
        if not project:
            # Only create brand-new projects — NEVER modify existing ones
            project = Project(
                title=proj_display_name,
                slug=slug,
                description=f"Project details for {proj_display_name}",
                is_featured=False,
                category_id=cat_id,
                status=\'published\'
            )
            db.session.add(project)
            db.session.flush()

        # Get filenames already saved for this project in DB
        existing_filenames = {img.filename for img in project.images}
        has_cover = any(img.is_cover for img in project.images)

        for num, filename, _ in items:
            src_path = os.path.join(images_dir, filename)
            dest_path = os.path.join(upload_dir, filename)

            # Copy file to uploads folder if not already there
            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
            elif os.path.getmtime(src_path) > os.path.getmtime(dest_path):
                shutil.copy2(src_path, dest_path)

            # ONLY add images not already in DB — NEVER modify existing DB records
            if filename not in existing_filenames:
                assign_cover = (num == 1) and not has_cover
                if assign_cover:
                    has_cover = True
                pi = ProjectImage(
                    project_id=project.id,
                    filename=filename,
                    is_cover=assign_cover,
                    sort_order=num
                )
                db.session.add(pi)

    db.session.commit()

@app.before_request
def auto_sync():
    sync_images_folder()
'''

# Find boundaries
import_shutil_pos = content.find('\nimport shutil\nfrom collections import defaultdict')
login_manager_pos = content.find('\nlogin_manager = LoginManager()')

if import_shutil_pos == -1 or login_manager_pos == -1:
    print('ERROR: Markers not found!')
else:
    before = content[:import_shutil_pos]
    after = content[login_manager_pos:]
    new_content = before + NEW_SYNC_BLOCK + after
    open('app.py', 'w', encoding='utf-8').write(new_content)
    print('Fixed successfully!')
