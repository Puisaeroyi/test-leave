import http from './http';

export const getEntities = async () => {
  const response = await http.get('/organizations/entities/');
  return response.data;
};

export const createEntity = async (data) => {
  const response = await http.post('/organizations/entities/create/', data);
  return response.data;
};

export const updateEntity = async (id, data) => {
  const response = await http.patch(`/organizations/entities/${id}/`, data);
  return response.data;
};

export const softDeleteEntity = async (id) => {
  const response = await http.patch(`/organizations/entities/${id}/soft-delete/`);
  return response.data;
};

export const getDeleteImpact = async (id) => {
  const response = await http.get(`/organizations/entities/${id}/delete-impact/`);
  return response.data;
};
