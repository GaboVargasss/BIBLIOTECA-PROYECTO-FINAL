document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname.includes('/libros')) {
    loadBooks();
    setupBookForm();
    setupEventListeners();
    setupReportHandlers();
  }
});

// ========== FUNCIONES PARA LIBROS ==========

function loadBooks(filters = {}) {
  let url = '/api/libros';
  const queryParams = new URLSearchParams();

  if (filters.author) queryParams.append('autor', filters.author);
  if (filters.category) queryParams.append('categoria', filters.category);

  if (queryParams.toString()) {
    url += `?${queryParams.toString()}`;
  }

  fetch(url)
    .then(response => {
      if (!response.ok) return [];
      return response.json();
    })
    .then(data => {
      const tbody = document.querySelector('#booksTable tbody');
      if (tbody) {
        tbody.innerHTML = '';

        data.forEach(book => {
          // Extraer el nombre de la categoría correctamente
          let categoryName = '—';
          
          if (book.category) {
            // Si category es un objeto (versión antigua de la API)
            if (typeof book.category === 'object' && book.category !== null) {
              categoryName = book.category.name || '—';
            } 
            // Si category es un string (versión nueva de la API)
            else if (typeof book.category === 'string') {
              categoryName = book.category;
            }
          } else if (book.category_id) {
            // Opcional: Si necesitas mostrar algo cuando hay category_id pero no category
            categoryName = 'Sin categoría';
          }

          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${book.id}</td>
            <td>${book.title}</td>
            <td>${book.author}</td>
            <td>${categoryName}</td>
            <td>
              ${window.userRole === 'admin'
                ? `<button onclick="editBook(${book.id})" class="btn btn-sm btn-warning">✏️ Editar</button>
                   <button onclick="confirmDelete(${book.id})" class="btn btn-sm btn-danger">🗑️ Eliminar</button>`
                : `<span class="text-muted">—</span>`
              }
            </td>`;
          tbody.appendChild(tr);
        });
      }
    })
    .catch(error => {
      console.error('Error loading books:', error);
    });
}
function setupBookForm() {
  const form = document.getElementById('bookForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (window.userRole !== 'admin') {
      alert('No autorizado');
      return;
    }

    const formData = {
      title: form.title.value,
      author: form.author.value,
      category: form.category.value,
      description: form.description.value
    };

    try {
      const bookId = form.dataset.id;
      const method = bookId ? 'PUT' : 'POST';
      const url = bookId ? `/api/libros/${bookId}` : '/api/libros';

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error en la operación');
      }

      const result = await response.json();
      alert(result.mensaje);
      
      form.reset();
      delete form.dataset.id;
      document.getElementById('formContainer').style.display = 'none';
      loadBooks();
    } catch (error) {
      console.error('Error:', error);
      alert(error.message || 'Error al guardar el libro');
    }
  });
}

function setupEventListeners() {
  document.getElementById('btnAddNew')?.addEventListener('click', () => {
    const form = document.getElementById('bookForm');
    form.reset();
    delete form.dataset.id;
    document.getElementById('formContainer').style.display = 'block';
    window.scrollTo({top: 0, behavior: 'smooth'});
  });

  document.getElementById('btnCancel')?.addEventListener('click', () => {
    document.getElementById('formContainer').style.display = 'none';
    document.getElementById('bookForm').reset();
    delete document.getElementById('bookForm').dataset.id;
  });
}

// ========== FUNCIONES PARA REPORTES ==========

function setupReportHandlers() {
  document.getElementById('btnLoanHistory')?.addEventListener('click', () => {
    fetchUsers().then(users => {
      showUserSelectionModal(users, 'Historial de préstamos', generateLoanHistoryReport);
    });
  });

  document.getElementById('btnAvailableCopies')?.addEventListener('click', () => {
    generateAvailableCopiesReport();
  });

  document.getElementById('btnActiveLoans')?.addEventListener('click', () => {
    generateActiveLoansReport();
  });

  document.getElementById('btnTopBorrowers')?.addEventListener('click', () => {
    generateTopBorrowersReport();
  });
}

// ========== FUNCIONES AUXILIARES ==========

async function fetchUsers() {
  try {
    const response = await fetch('/api/usuarios');
    if (!response.ok) throw new Error('Error al obtener usuarios');
    return await response.json();
  } catch (error) {
    console.error('Error:', error);
    showError('No se pudieron cargar los usuarios');
    return [];
  }
}

function showModal(content) {
  const modal = document.getElementById('reportModal') || document.createElement('div');
  modal.id = 'reportModal';
  modal.className = 'modal fade';
  modal.innerHTML = `
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        ${content}
      </div>
    </div>
  `;
  
  if (!document.getElementById('reportModal')) {
    document.body.appendChild(modal);
  }
  
  if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
    new bootstrap.Modal(modal).show();
  } else {
    modal.style.display = 'block';
  }
}

function showUserSelectionModal(users, title, callback) {
  const modalContent = `
    <div class="modal-header">
      <h5 class="modal-title">${title}</h5>
      <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
    </div>
    <div class="modal-body">
      <select id="userSelect" class="form-select">
        ${users.map(u => `
          <option value="${u.id}">${u.nombre} ${u.apellido} (${u.ci})</option>
        `).join('')}
      </select>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
      <button type="button" class="btn btn-primary" id="confirmSelection">Continuar</button>
    </div>
  `;
  
  const modal = showModal(modalContent);
  
  document.getElementById('confirmSelection').addEventListener('click', () => {
    const userId = document.getElementById('userSelect').value;
    callback(userId);
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
      bootstrap.Modal.getInstance(modal).hide();
    } else {
      modal.style.display = 'none';
    }
  });
}

function showLoading(message) {
  const loadingDiv = document.getElementById('loadingIndicator') || document.createElement('div');
  loadingDiv.id = 'loadingIndicator';
  loadingDiv.innerHTML = `
    <div class="loading-overlay">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Cargando...</span>
      </div>
      <p>${message}</p>
    </div>
  `;
  loadingDiv.style.position = 'fixed';
  loadingDiv.style.top = '0';
  loadingDiv.style.left = '0';
  loadingDiv.style.width = '100%';
  loadingDiv.style.height = '100%';
  loadingDiv.style.backgroundColor = 'rgba(0,0,0,0.5)';
  loadingDiv.style.display = 'flex';
  loadingDiv.style.justifyContent = 'center';
  loadingDiv.style.alignItems = 'center';
  loadingDiv.style.zIndex = '9999';
  loadingDiv.style.color = 'white';
  
  if (!document.getElementById('loadingIndicator')) {
    document.body.appendChild(loadingDiv);
  }
}

function hideLoading() {
  const loadingDiv = document.getElementById('loadingIndicator');
  if (loadingDiv) {
    loadingDiv.remove();
  }
}

function showError(message) {
  const errorDiv = document.createElement('div');
  errorDiv.className = 'alert alert-danger';
  errorDiv.textContent = message;
  
  const container = document.getElementById('errorContainer') || document.body;
  container.prepend(errorDiv);
  
  setTimeout(() => errorDiv.remove(), 5000);
}

// ========== GENERADORES DE REPORTES ==========

async function generateUserLoansReportFinal(userId) {
  try {
    showLoading('Generando reporte...');
    
    const response = await fetch(`/api/reportes/historial-usuario/${userId}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Error ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Mostrar los datos en consola para depuración
    console.log('Datos recibidos:', data);
    
    // Mostrar en modal
    const modalContent = `
      <div class="modal-header">
        <h5 class="modal-title">Historial de ${data.usuario.nombre} ${data.usuario.apellido}</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <table class="table table-striped">
          <thead>
            <tr>
              <th>Fecha Préstamo</th>
              <th>Fecha Devolución</th>
              <th>Estado</th>
              <th>Precio</th>
            </tr>
          </thead>
          <tbody>
            ${data.prestamos.map(p => `
              <tr>
                <td>${p.fecha_prestamo || '—'}</td>
                <td>${p.fecha_devolucion || 'Pendiente'}</td>
                <td>${p.estado || '—'}</td>
                <td>${p.precio?.toFixed(2) || '0.00'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
        <button type="button" class="btn btn-primary" onclick="downloadReport('user-history', ${userId})">
          Descargar PDF
        </button>
      </div>
    `;
    
    showModal(modalContent);
    
  } catch (error) {
    console.error('Error al generar reporte:', error);
    showError(error.message || 'Error al generar el reporte');
    
    // Mostrar detalles adicionales del error
    if (error.response) {
      console.error('Respuesta del servidor:', await error.response.json());
    }
  } finally {
    hideLoading();
  }
}

function displayLoanHistory(data) {
  const content = `
    <div class="modal-header">
      <h5 class="modal-title">Historial de: ${data.usuario.nombre} ${data.usuario.apellido}</h5>
      <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
    </div>
    <div class="modal-body">
      <table class="table table-striped">
        <thead>
          <tr>
            <th>Fecha Préstamo</th>
            <th>Fecha Devolución</th>
            <th>Estado</th>
            <th>Precio</th>
          </tr>
        </thead>
        <tbody>
          ${data.prestamos.map(p => `
            <tr>
              <td>${p.fecha_prestamo || '—'}</td>
              <td>${p.fecha_devolucion || 'Pendiente'}</td>
              <td>${p.estado || '—'}</td>
              <td>${p.precio ? p.precio.toFixed(2) : '0.00'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
      <button type="button" class="btn btn-primary" onclick="downloadReport('loan-history', ${data.usuario.id})">
        Descargar PDF
      </button>
    </div>
  `;
  
  showModal(content);
}

async function generateAvailableCopiesReport() {
  try {
    showLoading('Generando reporte...');
    
    const response = await fetch('/api/reportes/inventario');
    if (!response.ok) throw new Error('Error al obtener inventario');
    
    const data = await response.json();
    displayInventory(data);
    
  } catch (error) {
    console.error('Error:', error);
    showError(error.message || 'Error al generar el reporte');
  } finally {
    hideLoading();
  }
}

function displayInventory(data) {
  const content = `
    <div class="modal-header">
      <h5 class="modal-title">Inventario de libros</h5>
      <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
    </div>
    <div class="modal-body">
      <table class="table table-striped">
        <thead>
          <tr>
            <th>Título</th>
            <th>Autor</th>
            <th>Disponibles</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          ${data.map(item => `
            <tr>
              <td>${item.titulo || '—'}</td>
              <td>${item.autor || '—'}</td>
              <td>${item.copias_disponibles || 0}</td>
              <td>${item.copias_totales || 0}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
      <button type="button" class="btn btn-primary" onclick="downloadReport('inventory')">
        Descargar PDF
      </button>
    </div>
  `;
  
  showModal(content);
}

async function generateActiveLoansReport() {
  try {
    showLoading('Generando reporte...');
    
    const response = await fetch('/api/reportes/prestamos-activos');
    if (!response.ok) throw new Error('Error al obtener préstamos activos');
    
    const data = await response.json();
    displayActiveLoans(data);
    
  } catch (error) {
    console.error('Error:', error);
    showError(error.message || 'Error al generar el reporte');
  } finally {
    hideLoading();
  }
}

function displayActiveLoans(data) {
  const content = `
    <div class="modal-header">
      <h5 class="modal-title">Préstamos activos</h5>
      <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
    </div>
    <div class="modal-body">
      <table class="table table-striped">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>C.I.</th>
            <th>Días prestado</th>
            <th>Fecha préstamo</th>
          </tr>
        </thead>
        <tbody>
          ${data.map(loan => `
            <tr>
              <td>${loan.usuario_nombre || '—'}</td>
              <td>${loan.usuario_ci || '—'}</td>
              <td>${loan.dias_prestado || 0}</td>
              <td>${loan.fecha_prestamo || '—'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
      <button type="button" class="btn btn-primary" onclick="downloadReport('active-loans')">
        Descargar PDF
      </button>
    </div>
  `;
  
  showModal(content);
}

async function generateTopBorrowersReport() {
  try {
    showLoading('Generando reporte...');
    
    const response = await fetch('/api/reportes/top-usuarios');
    if (!response.ok) throw new Error('Error al obtener datos');
    
    const data = await response.json();
    displayTopBorrowers(data);
    
  } catch (error) {
    console.error('Error:', error);
    showError(error.message || 'Error al generar el reporte');
  } finally {
    hideLoading();
  }
}

function displayTopBorrowers(data) {
  const content = `
    <div class="modal-header">
      <h5 class="modal-title">Top usuarios con más préstamos</h5>
      <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
    </div>
    <div class="modal-body">
      <table class="table table-striped">
        <thead>
          <tr>
            <th>#</th>
            <th>Usuario</th>
            <th>C.I.</th>
            <th>Total préstamos</th>
          </tr>
        </thead>
        <tbody>
          ${data.map((user, index) => `
            <tr>
              <td>${index + 1}</td>
              <td>${user.nombre || '—'}</td>
              <td>${user.ci || '—'}</td>
              <td>${user.total_prestamos || 0}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
      <button type="button" class="btn btn-primary" onclick="downloadReport('top-borrowers')">
        Descargar PDF
      </button>
    </div>
  `;
  
  showModal(content);
}

// ========== FUNCIONES GLOBALES ==========

window.editBook = async function(id) {
  try {
    const response = await fetch(`/api/libros/${id}`);
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Libro no encontrado');
    }
    
    const book = await response.json();
    const form = document.getElementById('bookForm');
    
    form.title.value = book.title;
    form.author.value = book.author;
    form.category.value = book.category_id || '';
    form.description.value = book.description || '';
    form.dataset.id = book.id;
    
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.textContent = 'Actualizar Libro';
    
    document.getElementById('formContainer').style.display = 'block';
    window.scrollTo({top: 0, behavior: 'smooth'});
  } catch (error) {
    console.error('Error al editar libro:', error);
    alert(error.message || 'Error al cargar el libro para edición');
  }
};

window.confirmDelete = async function(id) {
  try {
    const roleResponse = await fetch('/api/user/role');
    const roleData = await roleResponse.json();
    
    if (roleData.role !== 'admin') {
      alert('No tienes permisos para eliminar libros');
      return;
    }

    if (confirm('¿Estás seguro de que deseas eliminar este libro?')) {
      await deleteBook(id);
    }
  } catch (error) {
    console.error('Error al verificar permisos:', error);
  }
};

async function deleteBook(id) {
  try {
    const response = await fetch(`/api/libros/${id}`, {
      method: 'DELETE',
      credentials: 'include'
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Error al eliminar');
    }

    const result = await response.json();
    alert(result.mensaje);
    loadBooks();
  } catch (error) {
    console.error('Error al eliminar libro:', error);
    alert(error.message || 'Error al eliminar el libro');
  }
}

window.downloadReport = function(type, id) {
  window.open(`/api/reportes/descargar?type=${type}&id=${id || ''}`, '_blank');
};