const form = document.getElementById('appointment-form');  
const dateInput = document.getElementById('date');  
const timeSelect = document.getElementById('time');  
const specialistSelect = document.getElementById('specialist');  
const serviceSelect = document.getElementById('service');  
const strizhkaTypeWrapper = document.getElementById('strizhkaTypeWrapper');  
const strizhkaTypeSelect = document.getElementById('strizhka-type');  
const nameInput = document.getElementById('name');  
const phoneInput = document.getElementById('phone');  

// Модальное окно и элементы внутри него  
const confirmationModal = document.getElementById('confirmationModal');  
const modalInfo = document.getElementById('modalInfo');  
const closeModalBtn = document.getElementById('closeModalBtn');  

// ------------------------------------------  
// Исходные данные для селектов  
// ------------------------------------------  
const specialists = [  
  'Иван Иванов. Стаж 5 лет. Мастер по укладкам и необычным стрижкам.',  
  'Петр Петров. Стаж 7 лет. Сделает из вашей бороды конфетку.',  
  'Сергей Сергеев. Стаж 3 года. Умеет и в маникюр и в стрижки. Универсальный солдат :)'  
];  
const services = ['Стрижка', 'Бритье', 'Маникюр'];  
const strizhkaOptions = ['Ножницами', 'Под машинку', 'Стрижка + укладка'];  

// ------------------------------------------  
// 1) Инициализируем элементы select  
// ------------------------------------------  
function initSelectOptions() {  
  // Специалисты  
  specialists.forEach(item => {  
    const option = document.createElement('option');  
    option.value = item;  
    option.textContent = item;  
    specialistSelect.appendChild(option);  
  });  

  // Услуги  
  services.forEach(item => {  
    const option = document.createElement('option');  
    option.value = item;  
    option.textContent = item;  
    serviceSelect.appendChild(option);  
  });  

  // Тип стрижки  
  strizhkaTypeSelect.innerHTML = '';  
  strizhkaOptions.forEach(item => {  
    const option = document.createElement('option');  
    option.value = item;  
    option.textContent = item;  
    strizhkaTypeSelect.appendChild(option);  
  });  

  // По умолчанию тип стрижки скрыт  
  strizhkaTypeWrapper.style.display = 'none';  
}  

// ------------------------------------------  
// 2) Отображение «Тип стрижки» только при выборе "Стрижка"  
// ------------------------------------------  
serviceSelect.addEventListener('change', () => {  
  if (serviceSelect.value === 'Стрижка') {  
    strizhkaTypeWrapper.style.display = 'block';  
  } else {  
    strizhkaTypeWrapper.style.display = 'none';  
  }  
});  

// ------------------------------------------  
// 3) Загрузка доступных слотов даты  
// ------------------------------------------  
dateInput.addEventListener('change', () => {  
  const selectedDate = dateInput.value;  
  if (!selectedDate) return;  

  // Очищаем текущее содержимое timeSelect  
  timeSelect.innerHTML = '';  

  // Добавим заглушку  
  const placeholderOption = document.createElement('option');  
  placeholderOption.value = '';  
  placeholderOption.textContent = '-- выберите время --';  
  timeSelect.appendChild(placeholderOption);  

  // Запрашиваем доступные слоты  
  fetchAvailableSlots(selectedDate)  
    .then(slots => {  
      slots.forEach(time => {  
        const option = document.createElement('option');  
        option.value = time;  
        option.textContent = time;  
        timeSelect.appendChild(option);  
      });  
    })  
    .catch(error => {  
      console.error('Ошибка при получении слотов:', error);  
      alert('Произошла ошибка при получении доступных слотов, попробуйте снова.');  
    });  
});  

// ------------------------------------------  
// 4) Обработка отправки формы  
// ------------------------------------------  
form.addEventListener('submit', event => {  
  event.preventDefault();  

  const formData = new FormData(form);  
  const date = formData.get('date');  
  const time = formData.get('time');  
  const specialist = formData.get('specialist');  
  const service = formData.get('service');  
  const strizhkaType = formData.get('strizhka-type');  
  const name = formData.get('name');  
  const phone = formData.get('phone');  

  // Валидация полей  
  if (!validateFields(date, time, specialist, service, name, phone)) {  
    return;  
  }  

  // Отправляем данные на сервер  
  createAppointment({  
    date,  
    time,  
    specialist,  
    service,  
    strizhkaType,  
    name,  
    phone  
  })  
    .then(response => {  
      console.log('Сервер ответил:', response);  
      // Показываем модальное окно  
      showConfirmationModal({  
        date,  
        time,  
        specialist,  
        service,  
        strizhkaType,  
        name,  
        phone  
      });  
    })  
    .catch(error => {  
      console.error('Ошибка при отправке данных:', error);  
      alert('Произошла ошибка при записи, попробуйте снова.');  
    });  
});  

// ------------------------------------------  
// 5) Клик по кнопке "Закрыть" в модальном окне  
// ------------------------------------------  
closeModalBtn.addEventListener('click', () => {  
  confirmationModal.style.display = 'none';  
  // Сброс формы  
  form.reset();  
  // Скрываем блок типа стрижки, если не возвращаемся к услуге "Стрижка"  
  strizhkaTypeWrapper.style.display = 'none';  
});  

// ------------------------------------------  
// 6) Инициализация селектов при загрузке  
// ------------------------------------------  
initSelectOptions();  

// ------------------------------------------  
// Функции валидации и работы с сервером  
// ------------------------------------------  

// Проверка полей формы  
function validateFields(date, time, specialist, service, name, phone) {  
  // Проверка телефона  
  const phoneRegex = /^\+?\d{1,3}?[-\s]?\(?\d{1,3}\)?[-\s]?\d{3,4}[-\s]?\d{4}$/;  
  if (!phoneRegex.test(phone)) {  
    alert('Пожалуйста, введите корректный номер телефона.');  
    return false;  
  }  

  // Проверка ФИО  
  const nameRegex = /^[а-яА-ЯёЁ\s]+$/;  
  if (!nameRegex.test(name)) {  
    alert('Пожалуйста, введите корректное ФИО (только кириллица).');  
    return false;  
  }  

  // Проверка заполненности  
  if (!date || !time || !specialist || !service || !name || !phone) {  
    alert('Пожалуйста, заполните все обязательные поля!');  
    return false;  
  }  

  return true;  
}  

// Получение доступных слотов  
async function fetchAvailableSlots(date) {  
  try {  
    const response = await fetch(`/available-slots?date=${date}`);  
    const data = await response.json();  
    return data.slots;  
  } catch (error) {  
    console.error('Ошибка при получении доступных слотов:', error);  
    throw error;  
  }  
}  

// Создание записи на сервере  
async function createAppointment(appointmentData) {  
  try {  
    const response = await fetch('/appointment', {  
      method: 'POST',  
      headers: {  
        'Content-Type': 'application/json'  
      },  
      body: JSON.stringify(appointmentData)  
    });  
    const data = await response.json();  
    return data;  
  } catch (error) {  
    console.error('Ошибка при отправке данных:', error);  
    throw error;  
  }  
}  

// Показать модальное окно  
function showConfirmationModal({ date, time, specialist, service, strizhkaType, name, phone }) {  
  let detailsHtml = `  
    <strong>Дата:</strong> ${date}<br/>  
    <strong>Время:</strong> ${time}<br/>  
    <strong>Специалист:</strong> ${specialist}<br/>  
    <strong>Услуга:</strong> ${service}<br/>  
  `;  
  if (service === 'Стрижка') {  
    detailsHtml += `<strong>Тип стрижки:</strong> ${strizhkaType}<br/>`;  
  }  
  detailsHtml += `  
    <strong>ФИО:</strong> ${name}<br/>  
    <strong>Телефон:</strong> ${phone}<br/><br/>  
    <span style="color: green; font-weight: bold;">Запись успешно создана!</span>  
  `;  

  modalInfo.innerHTML = detailsHtml;  
  confirmationModal.style.display = 'flex';  
}