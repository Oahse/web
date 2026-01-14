import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Input } from '../../forms/Input';
import { Textarea } from '../../forms/Textarea';
import { Button } from '../../ui/Button';

const productSchema = z.object({
  name: z.string().min(1, 'Product name is required'),
  description: z.string().optional(),
  short_description: z.string().optional(),
  product_status: z.string().optional(),
});

export const ProductEditForm = ({ product, onSubmit, loading }) => {
  const { control, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(productSchema),
    defaultValues: {
      name: product.name,
      description: product.description,
      short_description: product.short_description,
      product_status: product.product_status,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="grid grid-cols-1 gap-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Product Name
          </label>
          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <Input id="name" {...field} />
            )}
          />
          {errors.name && <p className="mt-2 text-sm text-red-600">{errors.name.message}</p>}
        </div>
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700">
            Description
          </label>
          <Controller
            name="description"
            control={control}
            render={({ field }) => (
              <Textarea id="description" {...field} />
            )}
          />
        </div>
        <div>
          <label htmlFor="short_description" className="block text-sm font-medium text-gray-700">
            Short Description
          </label>
          <Controller
            name="short_description"
            control={control}
            render={({ field }) => (
              <Textarea id="short_description" {...field} />
            )}
          />
        </div>
        <div>
          <label htmlFor="product_status" className="block text-sm font-medium text-gray-700">
            Product Status
          </label>
          <Controller
            name="product_status"
            control={control}
            render={({ field }) => (
              <select id="product_status" {...field} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
                <option>active</option>
                <option>inactive</option>
                <option>draft</option>
                <option>discontinued</option>
              </select>
            )}
          />
        </div>
        <div>
          <Button type="submit" disabled={loading}>
            {loading ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>
    </form>
  );
};
