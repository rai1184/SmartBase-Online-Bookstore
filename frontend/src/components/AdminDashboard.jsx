import { useState, useRef } from "react";
import { adminAddBookApi, adminUpdateBookApi, adminDeleteBookApi, adminUploadImageApi } from "../services/api";

export default function AdminDashboard({ user, books, refreshBooks }) {
  const [filterText, setFilterText] = useState("");
  const [editingIsbn, setEditingIsbn] = useState(null);
  
  // Track whether an uploaded file is currently locking the URL text input
  const [isUploaded, setIsUploaded] = useState(false);
  
  // Reference to reset the native file input element
  const fileInputRef = useRef(null);
  
  // Form state
  const [formData, setFormData] = useState({
    isbn: "",
    title: "",
    author: "",
    about: "",
    msrp: "",
    publication_date: "",
    genre_id: "10",
    cover_image: "",
    in_stock: "10",
    page_count: "300"
  });
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  if (!user || !user.is_admin) {
    return (
      <div className="page">
        <div className="empty-message">
          <h3>Access Denied</h3>
          <p>You must be logged in as an administrator to view this page.</p>
        </div>
      </div>
    );
  }

  // Local front-end filtering by book title or author
  const filteredBooks = books.filter((b) => 
    b.Title.toLowerCase().includes(filterText.toLowerCase()) ||
    b.Author.toLowerCase().includes(filterText.toLowerCase())
  );

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    // If typing manually into the cover_image input, ensure upload lock is released
    if (name === "cover_image") {
      setIsUploaded(false);
    }
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      setErrorMsg("");
      const userId = user.user_id || user.id;
      const res = await adminUploadImageApi(file, userId);
      
      // Update filename and lock the text input
      setFormData((prev) => ({ ...prev, cover_image: res.filename }));
      setIsUploaded(true);
      setSuccessMsg("Image uploaded successfully!");
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleEditClick = (book) => {
    setEditingIsbn(book.ISBN);
    setFormData({
      isbn: book.ISBN,
      title: book.Title,
      author: book.Author,
      about: book.About || "",
      msrp: book.MSRP || "",
      publication_date: book.PublicationDate || "",
      genre_id: book.GenreId || "10",
      cover_image: book.CoverImage || "",
      in_stock: book.InStock ?? 0,
      page_count: book.Pages || 0
    });
    setIsUploaded(false); // Unlock for editing
    if (fileInputRef.current) fileInputRef.current.value = "";
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCancelEdit = () => {
    setEditingIsbn(null);
    setIsUploaded(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setFormData({
      isbn: "", title: "", author: "", about: "", msrp: "",
      publication_date: "", genre_id: "10", cover_image: "", in_stock: "10", page_count: "300"
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const payload = {
        ...formData,
        msrp: parseFloat(formData.msrp),
        in_stock: parseInt(formData.in_stock, 10),
        page_count: parseInt(formData.page_count, 10),
        genre_id: parseInt(formData.genre_id, 10)
      };

      const userId = user.user_id || user.id;

      if (editingIsbn) {
        await adminUpdateBookApi(editingIsbn, payload, userId);
        setSuccessMsg("Book updated successfully!");
      } else {
        await adminAddBookApi(payload, userId);
        setSuccessMsg("New book added successfully!");
      }

      refreshBooks();
      handleCancelEdit();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleDelete = async (isbn) => {
    if (!window.confirm(`Are you sure you want to delete book ISBN ${isbn}?`)) return;
    try {
      const userId = user.user_id || user.id;
      await adminDeleteBookApi(isbn, userId);
      refreshBooks();
      setSuccessMsg("Book deleted successfully.");
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  return (
    <div className="page">
      <div className="page-heading">
        <p className="section-label">ADMINISTRATION</p>
        <h1>Book Inventory Dashboard</h1>
        <p>Add new titles, edit existing details, update stock numbers, or remove items from the catalog.</p>
      </div>

      {errorMsg && <div className="auth-error"><p>{errorMsg}</p></div>}
      {successMsg && <div style={{ color: "var(--color-success)", marginBottom: "15px", fontWeight: "bold" }}>{successMsg}</div>}

      {/* Add / Edit Form */}
      <div className="search-container" style={{ marginBottom: "40px" }}>
        <h3 style={{ gridColumn: "1 / -1", margin: 0, fontFamily: "Georgia, serif", fontSize: "20px" }}>
          {editingIsbn ? `Edit Book: ${editingIsbn}` : "Add New Book"}
        </h3>
        <form onSubmit={handleSubmit} style={{ display: "contents" }}>
          <label>
            ISBN
            <input 
              name="isbn" 
              value={formData.isbn} 
              onChange={handleInputChange} 
              disabled={editingIsbn !== null} 
              placeholder="978-0000000000" 
              required 
            />
          </label>
          <label>
            Title
            <input name="title" value={formData.title} onChange={handleInputChange} placeholder="Book Title" required />
          </label>
          <label>
            Author
            <input name="author" value={formData.author} onChange={handleInputChange} placeholder="Author Name" required />
          </label>
          <label>
            MSRP ($)
            <input type="number" step="0.01" name="msrp" value={formData.msrp} onChange={handleInputChange} placeholder="19.99" required />
          </label>
          <label>
            Genre ID (10=SciFi, 11=Fantasy, etc.)
            <input type="number" name="genre_id" value={formData.genre_id} onChange={handleInputChange} />
          </label>
          <label>
            In Stock Count
            <input type="number" name="in_stock" value={formData.in_stock} onChange={handleInputChange} />
          </label>
          <label>
            Page Count
            <input type="number" name="page_count" value={formData.page_count} onChange={handleInputChange} />
          </label>
          
          {/* Cover Image URL / File Upload Input with Lock & Clear Logic */}
          <label style={{ gridColumn: "1 / -1" }}>
            Cover Image (Paste URL or Upload File)
            <div style={{ display: "flex", gap: "10px", alignItems: "center", marginTop: "4px" }}>
              <input 
                name="cover_image" 
                value={formData.cover_image} 
                onChange={handleInputChange} 
                disabled={isUploaded}
                placeholder={isUploaded ? "File uploaded (URL input locked)" : "https://example.com/image.jpg"} 
                style={{ 
                  flex: 2, 
                  padding: "8px", 
                  border: "1px solid var(--color-border-strong)", 
                  borderRadius: "4px",
                  backgroundColor: isUploaded ? "#f5f5f5" : "white",
                  color: isUploaded ? "#666" : "inherit"
                }}
              />
              {isUploaded && (
                <button 
                  type="button" 
                  onClick={() => {
                    setIsUploaded(false);
                    if (fileInputRef.current) fileInputRef.current.value = "";
                    setFormData((prev) => ({ ...prev, cover_image: "" }));
                  }}
                  style={{ padding: "8px 12px", fontSize: "12px", background: "var(--color-surface)", border: "1px solid var(--color-border-strong)", borderRadius: "4px", cursor: "pointer" }}
                  title="Unlock text input and clear uploaded image"
                >
                  Switch to URL
                </button>
              )}
              <input 
                ref={fileInputRef}
                type="file" 
                accept="image/png, image/jpeg, image/webp, image/gif" 
                onChange={handleImageUpload} 
                style={{ flex: 1, padding: "5px", border: "1px solid var(--color-border-strong)", borderRadius: "4px", background: "white", fontSize: "12px" }}
              />
            </div>
            {formData.cover_image && (
              <span style={{ fontSize: "12px", color: "var(--color-ink-soft)", display: "block", marginTop: "4px" }}>
                Current value: <strong>{formData.cover_image}</strong> {isUploaded && "(Uploaded File)"}
              </span>
            )}
          </label>

          <label style={{ gridColumn: "1 / -1" }}>
            About / Description
            <textarea name="about" value={formData.about} onChange={handleInputChange} rows="3" style={{ width: "100%", padding: "8px", border: "1px solid var(--color-border-strong)", borderRadius: "4px" }} />
          </label>

          <div style={{ gridColumn: "1 / -1", display: "flex", gap: "10px", marginTop: "10px" }}>
            <button type="submit" className="standard-button" style={{ margin: 0 }}>
              {editingIsbn ? "Save Changes" : "Add Book to Catalog"}
            </button>
            {editingIsbn && (
              <button type="button" className="browse-button" onClick={handleCancelEdit}>
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Local Filter Bar */}
      <div style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <h2 style={{ margin: 0, fontFamily: "Georgia, serif", fontSize: "24px" }}>Manage Catalog</h2>
        <input 
          type="text" 
          placeholder="Filter books by title or author locally..." 
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          style={{ width: "300px", padding: "10px", borderRadius: "4px", border: "1px solid var(--color-border-strong)" }}
        />
      </div>

      {/* Book Management Grid */}
      <div className="book-grid">
        {filteredBooks.length > 0 ? (
          filteredBooks.map((book) => (
            <div key={book.ISBN} className="book-card" style={{ padding: "16px", display: "flex", flexDirection: "column" }}>
              <h4>{book.Title}</h4>
              <p className="book-author">by {book.Author}</p>
              <p style={{ fontSize: "12px", color: "var(--color-ink-soft)" }}>ISBN: {book.ISBN}</p>
              <p style={{ fontSize: "12px" }}>Stock: <strong>{book.InStock ?? 0}</strong> | Price: <strong>${book.MSRP?.toFixed(2)}</strong></p>
              
              <div style={{ display: "flex", gap: "8px", marginTop: "auto", paddingTop: "12px" }}>
                <button className="browse-button" onClick={() => handleEditClick(book)} style={{ flex: 1, padding: "6px" }}>
                  Edit
                </button>
                <button className="browse-button" onClick={() => handleDelete(book.ISBN)} style={{ flex: 1, padding: "6px", color: "var(--color-danger)", borderColor: "var(--color-danger)" }}>
                  Delete
                </button>
              </div>
            </div>
          ))
        ) : (
          <p>No matching books found.</p>
        )}
      </div>
    </div>
  );
}