document.addEventListener('DOMContentLoaded',()=>{
  if (window.location.pathname.includes('/libros')) {
    loadBooks();
    setupBookForm();
  }
});

function loadBooks(){
  fetch('/api/books')
    .then(r=>r.json())
    .then(data=>{
      const tbody = document.querySelector('#booksTable tbody');
      tbody.innerHTML = '';
      data.forEach(b=>{
        const tr=document.createElement('tr');
        tr.innerHTML=`
          <td>${b.id}</td>
          <td>${b.title}</td>
          <td>${b.author}</td>
          <td>${b.category||''}</td>
          <td>
            ${window.userRole==='admin'
              ? `<button onclick="editBook(${b.id})" class="btn btn-sm btn-warning">✏️</button>
                 <button onclick="deleteBook(${b.id})" class="btn btn-sm btn-danger">🗑️</button>`
              : `<span class="text-muted">—</span>`
            }
          </td>`;
        tbody.appendChild(tr);
      });
    });
}

function setupBookForm(){
  const form = document.getElementById('bookForm');
  if (!form) return;
  form.addEventListener('submit',e=>{
    e.preventDefault();
    if (window.userRole!=='admin') return alert('No autorizado');
    const id = form.dataset.id;
    const payload = {
      title: form.title.value,
      author: form.author.value,
      description: form.description.value,
      category_id: parseInt(form.category.value)
    };
    const url    = id?`/api/books/${id}`:'/api/books';
    const method = id?'PUT':'POST';
    fetch(url,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
      .then(r=>{
        if (r.ok) { form.reset(); delete form.dataset.id; loadBooks(); }
      });
  });
}

function editBook(id){
  fetch('/api/books').then(r=>r.json()).then(data=>{
    const book = data.find(b=>b.id===id);
    const form = document.getElementById('bookForm');
    form.title.value       = book.title;
    form.author.value      = book.author;
    form.description.value = book.description||'';
    form.category.value    = book.category_id||'';
    form.dataset.id        = id;
    window.scrollTo({top:0,behavior:'smooth'});
  });
}

function deleteBook(id){
  if (window.userRole!=='admin') return alert('No autorizado');
  fetch(`/api/books/${id}`,{method:'DELETE'})
    .then(r=>{ if (r.status===204) loadBooks(); });
}
