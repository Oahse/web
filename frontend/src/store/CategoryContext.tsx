import React, { createContext, useState, useEffect, useContext } from 'react';
import { useAsync } from '../hooks/useAsync';
import { CategoriesAPI } from '../apis';

interface Category {
  id: string;
  name: string;
}

interface CategoryContextType {
  categories: Category[];
  loading: boolean;
  error: any;
}

export const CategoryContext = createContext<CategoryContextType | undefined>(undefined);

export const CategoryProvider = ({ children }: { children: React.ReactNode }) => {
  const { loading, error, execute } = useAsync();
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    execute(async () => {
      const response = await CategoriesAPI.getCategories();
      // API returns { success: true, data: { categories: [...] } }
      const categoriesArray = response.data?.categories || response.categories || response.data || response;
      setCategories(Array.isArray(categoriesArray) ? categoriesArray : []);
      return response;
    });
  }, [execute]);

  return (
    <CategoryContext.Provider value={{ categories, loading, error }}>
      {children}
    </CategoryContext.Provider>
  );
};

export const useCategories = () => {
  const context = useContext(CategoryContext);
  if (context === undefined) {
    throw new Error('useCategory error: must be used within a CategoryProvider');
  }
  return context;
};