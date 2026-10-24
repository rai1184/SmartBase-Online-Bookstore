import { useState } from "react";

export default function SearchBox({
  onSearch,
  genres,
}) {
  const [query, setQuery] = useState({
    title: "",
    author: "",
    genre: "All",
    maxPrice: "",
    minRating: "",
    publicationYear: "",

    relaxTitle: true,
    relaxAuthor: true,
    relaxGenre: true,
    relaxPrice: true,
    relaxRating: true,
    relaxYear: true,
  });

  const update = (event) => {
    const { name, value, type, checked } =
      event.target;

    setQuery((current) => ({
      ...current,
      [name]:
        type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSearch(query);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="search-container"
    >
      <label>
        Title
        <input
          type="text"
          name="title"
          placeholder="Book title"
          value={query.title}
          onChange={update}
        />
      </label>

      <label>
        Author
        <input
          type="text"
          name="author"
          placeholder="Author name"
          value={query.author}
          onChange={update}
        />
      </label>

      <label>
        Genre
        <select
          name="genre"
          value={query.genre}
          onChange={update}
        >
          <option value="All">All Genres</option>

          {genres.map((genre) => (
            <option
              key={genre}
              value={genre}
            >
              {genre}
            </option>
          ))}
        </select>
      </label>

      <label>
        Maximum Price
        <input
          type="number"
          name="maxPrice"
          min="0"
          step="0.01"
          placeholder="Example: 30"
          value={query.maxPrice}
          onChange={update}
        />
      </label>

      <label>
        Minimum Rating
        <input
          type="number"
          name="minRating"
          min="0"
          max="5"
          step="0.1"
          placeholder="Example: 4.0"
          value={query.minRating}
          onChange={update}
        />
      </label>

      <label>
        Publication Year
        <input
          type="number"
          name="publicationYear"
          placeholder="Example: 2020"
          value={query.publicationYear}
          onChange={update}
        />
      </label>

      <div className="relaxation-box">
        <h3>Smart Alternative Settings</h3>

        <p>
          Select which requirements SmartBase may
          relax if an exact match is unavailable.
        </p>

        <label>
          <input
            type="checkbox"
            name="relaxTitle"
            checked={query.relaxTitle}
            onChange={update}
          />
          Title
        </label>

        <label>
          <input
            type="checkbox"
            name="relaxAuthor"
            checked={query.relaxAuthor}
            onChange={update}
          />
          Author
        </label>

        <label>
          <input
            type="checkbox"
            name="relaxGenre"
            checked={query.relaxGenre}
            onChange={update}
          />
          Genre
        </label>

        <label>
          <input
            type="checkbox"
            name="relaxPrice"
            checked={query.relaxPrice}
            onChange={update}
          />
          Price
        </label>

        <label>
          <input
            type="checkbox"
            name="relaxRating"
            checked={query.relaxRating}
            onChange={update}
          />
          Rating
        </label>

        <label>
          <input
            type="checkbox"
            name="relaxYear"
            checked={query.relaxYear}
            onChange={update}
          />
          Publication Year
        </label>
      </div>

      <button
        className="search-button"
        type="submit"
      >
        Search Books
      </button>
    </form>
  );
}