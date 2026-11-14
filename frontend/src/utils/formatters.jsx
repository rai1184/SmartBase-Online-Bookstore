// Turn DB result in readable object 
// Turn DB result into a readable frontend object
export const formatBook = (book) => ({
  ISBN: book.isbn,
  Title: book.title,
  Author: book.author,
  Genre: book.genre || "Uncategorized",
  MSRP: Number(book.msrp),
  Rating: book.avg_rating ?? null,
  ReviewCount: book.review_count ?? 0,
  Pages: null,
  PublicationYear: book.publication_date
    ? Number(book.publication_date.slice(0, 4))
    : null,
  About: book.about,
  CoverImage: book.cover_image
});