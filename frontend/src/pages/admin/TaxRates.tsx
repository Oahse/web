import React, { useState, useEffect } from 'react';
import { PlusIcon, PencilIcon, TrashIcon, SearchIcon, FilterIcon } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { Select } from '../../components/ui/Select';
import { SearchableSelect } from '../../components/ui/SearchableSelect';
import { getCountryOptions, getProvinceOptions, getCountryByCode } from '../../data/countries';
import TaxAPI, { TaxRate, TaxType, Country } from '../../apis/tax';

export const TaxRatesAdmin = () => {
  const [taxRates, setTaxRates] = useState<TaxRate[]>([]);
  const [countries, setCountries] = useState<Country[]>([]);
  const [taxTypes, setTaxTypes] = useState<TaxType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingRate, setEditingRate] = useState<TaxRate | null>(null);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [activeFilter, setActiveFilter] = useState<boolean | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    country_code: '',
    country_name: '',
    province_code: '',
    province_name: '',
    tax_rate: '',
    tax_name: '',
    is_active: true
  });

  useEffect(() => {
    fetchTaxRates();
    fetchCountries();
    fetchTaxTypes();
  }, [selectedCountry, activeFilter, searchTerm]);

  const fetchTaxRates = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (selectedCountry) params.country_code = selectedCountry;
      if (activeFilter !== null) params.is_active = activeFilter;
      if (searchTerm) params.search = searchTerm;
      params.per_page = 100;
      
      const data = await TaxAPI.getTaxRates(params);
      setTaxRates(data || []);
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to load tax rates');
    } finally {
      setLoading(false);
    }
  };

  const fetchCountries = async () => {
    try {
      const data = await TaxAPI.getCountriesWithTaxRates();
      setCountries(data || []);
    } catch (error) {
      console.error('Failed to load countries:', error);
    }
  };

  const fetchTaxTypes = async () => {
    try {
      const data = await TaxAPI.getAvailableTaxTypes();
      setTaxTypes(data || []);
    } catch (error) {
      console.error('Failed to load tax types:', error);
      // Fallback to basic tax types if API fails
      setTaxTypes([
        { value: 'VAT', label: 'VAT (Value Added Tax)', usage_count: 0 },
        { value: 'GST', label: 'GST (Goods and Services Tax)', usage_count: 0 },
        { value: 'Sales Tax', label: 'Sales Tax', usage_count: 0 },
        { value: 'IVA', label: 'IVA (Impuesto al Valor Agregado)', usage_count: 0 },
        { value: 'HST', label: 'HST (Harmonized Sales Tax)', usage_count: 0 },
        { value: 'Other', label: 'Other', usage_count: 0 }
      ]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const data = {
        country_code: formData.country_code.toUpperCase(),
        country_name: formData.country_name,
        province_code: formData.province_code ? formData.province_code.toUpperCase() : undefined,
        province_name: formData.province_name || undefined,
        tax_rate: parseFloat(formData.tax_rate) / 100, // Convert percentage to decimal
        tax_name: formData.tax_name || undefined,
        is_active: formData.is_active
      };

      if (editingRate) {
        await TaxAPI.updateTaxRate(editingRate.id, data);
        toast.success('Tax rate updated successfully');
      } else {
        await TaxAPI.createTaxRate(data);
        toast.success('Tax rate created successfully');
      }
      
      setShowModal(false);
      resetForm();
      fetchTaxRates();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to save tax rate');
    }
  };

  // Handle country selection and auto-populate country name
  const handleCountryChange = (countryCode: string) => {
    const country = getCountryByCode(countryCode);
    setFormData({
      ...formData,
      country_code: countryCode,
      country_name: country?.name || '',
      province_code: '', // Reset province when country changes
      province_name: ''
    });
  };

  // Handle province selection and auto-populate province name
  const handleProvinceChange = (provinceCode: string) => {
    const provinces = getProvinceOptions(formData.country_code);
    const province = provinces.find(p => p.value === provinceCode);
    setFormData({
      ...formData,
      province_code: provinceCode,
      province_name: province?.label || ''
    });
  };

  const handleEdit = (rate: TaxRate) => {
    setEditingRate(rate);
    setFormData({
      country_code: rate.country_code,
      country_name: rate.country_name,
      province_code: rate.province_code || '',
      province_name: rate.province_name || '',
      tax_rate: rate.tax_percentage.toString(),
      tax_name: rate.tax_name || '',
      is_active: rate.is_active
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this tax rate?')) return;
    
    try {
      await TaxAPI.deleteTaxRate(id);
      toast.success('Tax rate deleted successfully');
      fetchTaxRates();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to delete tax rate');
    }
  };

  const resetForm = () => {
    setFormData({
      country_code: '',
      country_name: '',
      province_code: '',
      province_name: '',
      tax_rate: '',
      tax_name: '',
      is_active: true
    });
    setEditingRate(null);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-copy">Tax Rates Management</h1>
        <button
          onClick={() => {
            resetForm();
            setShowModal(true);
          }}
          className="bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-dark flex items-center gap-2"
        >
          <PlusIcon size={20} />
          Add Tax Rate
        </button>
      </div>

      {/* Filters */}
      <div className="bg-surface rounded-lg shadow-sm p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-copy mb-2">
              <SearchIcon size={16} className="inline mr-1" />
              Search
            </label>
            <input
              type="text"
              placeholder="Search country or province..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-surface text-copy"
            />
          </div>
          
          <div>
            <Select
              label={
                <>
                  <FilterIcon size={16} className="inline mr-1" />
                  Country
                </>
              }
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              options={[
                { value: '', label: 'All Countries' },
                ...countries.map((country) => ({
                  value: country.country_code,
                  label: `${country.country_name} (${country.rate_count})`
                }))
              ]}
            />
          </div>
          
          <div>
            <Select
              label="Status"
              value={activeFilter === null ? '' : String(activeFilter)}
              onChange={(e) => setActiveFilter(e.target.value === '' ? null : e.target.value === 'true')}
              options={[
                { value: '', label: 'All' },
                { value: 'true', label: 'Active' },
                { value: 'false', label: 'Inactive' }
              ]}
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedCountry('');
                setActiveFilter(null);
              }}
              className="w-full px-4 py-2 border border-border rounded-md hover:bg-surface-hover text-copy"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Tax Rates Table */}
      <div className="bg-surface rounded-lg shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-copy-light">Loading...</div>
        ) : taxRates.length === 0 ? (
          <div className="p-8 text-center text-copy-light">No tax rates found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-background">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-copy uppercase tracking-wider">
                    Country
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-copy uppercase tracking-wider">
                    Province/State
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-copy uppercase tracking-wider">
                    Tax Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-copy uppercase tracking-wider">
                    Tax Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-copy uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-copy uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-light">
                {taxRates.map((rate) => (
                  <tr key={rate.id} className="hover:bg-surface-hover">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <img
                          src={`https://flagcdn.com/w20/${rate.country_code.toLowerCase()}.png`}
                          alt={rate.country_code}
                          className="w-5 h-auto mr-2"
                        />
                        <div>
                          <div className="text-sm font-medium text-copy">{rate.country_name}</div>
                          <div className="text-xs text-copy-light">{rate.country_code}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {rate.province_name ? (
                        <div>
                          <div className="text-sm text-copy">{rate.province_name}</div>
                          <div className="text-xs text-copy-light">{rate.province_code}</div>
                        </div>
                      ) : (
                        <span className="text-sm text-copy-light">National</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-copy">
                        {rate.tax_percentage.toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-copy">{rate.tax_name || '-'}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          rate.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {rate.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEdit(rate)}
                        className="text-primary hover:text-primary-dark mr-3"
                      >
                        <PencilIcon size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(rate.id)}
                        className="text-error hover:text-error-dark"
                      >
                        <TrashIcon size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-surface rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-2xl font-bold text-copy mb-6">
                {editingRate ? 'Edit Tax Rate' : 'Add Tax Rate'}
              </h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <SearchableSelect
                    label="Country"
                    placeholder="Search and select country..."
                    value={formData.country_code}
                    onChange={handleCountryChange}
                    options={getCountryOptions()}
                    required
                    disabled={!!editingRate}
                    allowClear={!editingRate}
                  />
                  
                  <div>
                    <label className="block text-sm font-medium text-copy mb-2">
                      Country Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.country_name}
                      onChange={(e) => setFormData({ ...formData, country_name: e.target.value })}
                      className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-surface text-copy"
                      placeholder="Auto-filled from country selection"
                      readOnly
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <SearchableSelect
                    label="Province/State"
                    placeholder="Search and select province/state..."
                    value={formData.province_code}
                    onChange={handleProvinceChange}
                    options={getProvinceOptions(formData.country_code)}
                    disabled={!!editingRate || !formData.country_code}
                    allowClear
                    noOptionsMessage={
                      !formData.country_code 
                        ? "Select a country first" 
                        : "No provinces/states available for this country"
                    }
                  />
                  
                  <div>
                    <label className="block text-sm font-medium text-copy mb-2">
                      Province/State Name
                    </label>
                    <input
                      type="text"
                      value={formData.province_name}
                      onChange={(e) => setFormData({ ...formData, province_name: e.target.value })}
                      className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-surface text-copy"
                      placeholder="Auto-filled from province selection"
                      readOnly
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-copy mb-2">
                      Tax Rate (%) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="100"
                      required
                      value={formData.tax_rate}
                      onChange={(e) => setFormData({ ...formData, tax_rate: e.target.value })}
                      className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-surface text-copy"
                      placeholder="7.25"
                    />
                  </div>
                  
                  <SearchableSelect
                    label="Tax Name"
                    placeholder="Search or type tax name..."
                    value={formData.tax_name}
                    onChange={(value) => setFormData({ ...formData, tax_name: value })}
                    options={taxTypes.map(type => ({
                      value: type.value,
                      label: `${type.label} (${type.usage_count} uses)`
                    }))}
                    allowClear
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
                  />
                  <label htmlFor="is_active" className="ml-2 block text-sm text-copy">
                    Active
                  </label>
                </div>

                <div className="flex justify-end gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      resetForm();
                    }}
                    className="px-4 py-2 border border-border rounded-md hover:bg-surface-hover text-copy"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark"
                  >
                    {editingRate ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaxRatesAdmin;
