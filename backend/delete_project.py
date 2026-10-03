import os
from app import app, db
from models import Project, Category, ProjectImage, slugify

with app.app_context():
    # Delete the old project and its images
    old_project = Project.query.filter_by(title='Sparsh Hospital').first()
    if old_project:
        db.session.delete(old_project)
        db.session.commit()
    print("Deleted old project")
