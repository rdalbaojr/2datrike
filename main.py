# In your User Model (add these columns):
class User(Base):
    # ... existing columns ...
    city = Column(String, nullable=True, default="Pasig City")
    barangay = Column(String, nullable=True, default="")
    toda_name = Column(String, nullable=True, default="")
    branch = Column(String, default="Main") 

# Startup table alter check (inside initialize_config startup event):
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN city VARCHAR DEFAULT 'Pasig City'"))
        db.execute(text("ALTER TABLE users ADD COLUMN barangay VARCHAR DEFAULT ''"))
        db.execute(text("ALTER TABLE users ADD COLUMN toda_name VARCHAR DEFAULT ''"))
        db.commit()
    except Exception:
        db.rollback()

# In your register_account endpoint:
@app.post("/register-account/")
def register_account(
    role: str = Form(...), username: str = Form(...), password: str = Form(...),
    full_name: str = Form(...), address: str = Form(...), whatsapp_number: str = Form(...),
    toda_number: Optional[str] = Form(None), gcash_account: Optional[str] = Form(None), 
    bank_name: Optional[str] = Form("GCash"), 
    city: Optional[str] = Form("Pasig City"),
    barangay: Optional[str] = Form(""),
    toda_name: Optional[str] = Form(""),
    toda_id: Optional[UploadFile] = File(None), db: Session = Depends(get_db)
):
    clean_user = sanitize_name(username)
    clean_full_name = sanitize_name(full_name)
    
    existing_user = db.query(User).filter(User.username == clean_user).first()
    if existing_user: raise HTTPException(status_code=400, detail="Username already registered")

    file_path = None
    if role == "driver" and toda_id and toda_id.filename:
        file_path = f"uploads/{clean_user}_{toda_id.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(toda_id.file, buffer)

    # Automatically format branch name for admin filtering (e.g., "Pasig City - San Antonio (KOTA)")
    assigned_branch = f"{city} - {barangay} ({toda_name})" if role == "driver" else "Passenger"

    new_user = User(
        username=clean_user, password=password, role=role, full_name=clean_full_name,
        address=address, whatsapp_number=whatsapp_number, toda_number=toda_number,
        gcash_account=gcash_account, bank_name=bank_name, toda_id_path=file_path,
        city=city, barangay=barangay, toda_name=toda_name, branch=assigned_branch
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login.html", status_code=303)
