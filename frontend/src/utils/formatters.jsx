// Turn DB result in readable object 
export const formatBook = (book) => ({
  ISBN: book.isbn,
  Title: book.title,
  Author: book.author,
  Genre: book.genre || "Uncategorized",
  MSRP: Number(book.msrp),
  Rating: null,
  Pages: null,
  PublicationYear: book.publication_date
    ? Number(book.publication_date.slice(0, 4))
    : null,
  About: book.about,
  CoverImage: book.cover_image
});