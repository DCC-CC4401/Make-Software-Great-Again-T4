# -*- coding: utf-8 -*-
import datetime
import time

from django.db import IntegrityError
from django.contrib import auth
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from app.forms import LoginForm, EditarCuenta, EditarProductoForm, SignUpForm
from app.models import Usuario, Vendedor, Producto, VendedorFijo, FormasDePago, Alumno
from app.utils import agregar_usuario, agregar_vendedor_ambulante, agregar_vendedor_fijo


def index(request):
    return render(request, 'app/index.html')


def actualizar_atributo(clase, atributo):
    '''
    Entrega la lista actualizada del atributo correspondiente.
    :param clase: Class
    :param atributo: String
    :return: List[type:Class.atributo]
    '''

    list = []
    for atr in clase.objects.all().order_by(atributo).values_list(atributo):
        list.append((atr, atr))
    return list


class Login(View):
    @staticmethod
    def get(request):
        form = LoginForm()
        return render(request, 'app/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            self.get(request)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'app/login.html', {
                'login_message': 'Nombre de Usuario o Contraseña erroneos', 'form': form, })
        if not user.is_active:
            return render(request, 'app/login.html', {
                'login_message': 'Su cuenta ha sido banneada', 'form': form, })
        auth.login(request, user)
        return HttpResponseRedirect(reverse('home'))


def home(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))
    user = Usuario.objects.get(user=request.user)
    if user.tipo == 1:
        return render(request, 'app/home.html', {'user': user})
    vendor = Vendedor.objects.get(usuario=user)
    update(vendor)
    products = []
    raw_products = Producto.objects.filter(vendedor=vendor)
    schedule = VendedorFijo.objects.get(usuario=user).schedule() if user.tipo == 2 else None
    for p in raw_products:
        products.append(p)
    return render(request, 'app/vendedor-main.html', {'user': user, 'vendor': vendor,
                                                      'products': products, 'schedule': schedule})


def stock(request):
    return None


def stats(request):
    return None


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('index'))


def test(request):
    return render(request, 'app/test.html')


class SignUp(View):
    @staticmethod
    def get(request):
        choices = []
        for i in FormasDePago.objects.all().values():
            choices.append((i['metodo'], i['metodo']))
        form = SignUpForm()
        form.fields['formas_pago'].choices = choices
        return render(request, 'app/signup.html', {'form': form})

    @staticmethod
    def post(request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] != form.cleaned_data['repassword']:
                return render(request, 'app/signup.html', {'message':                                                               'Las contraseñas no coinciden', 'form': form})
            else:
                try:
                    tipo = form.cleaned_data['tipo']
                    if (tipo == "1"):
                        agregar_usuario(form.cleaned_data)
                    if (tipo == "2"):
                        if (form.cleaned_data['hora_ini'] is None):
                            raise KeyError('Ingresa hora de inicio')
                        if (form.cleaned_data['hora_fin' is None]):
                            raise KeyError('Ingresa hora de termino')
                        agregar_vendedor_fijo(form.cleaned_data)
                    if (tipo == "3"):
                        agregar_vendedor_ambulante(form.cleaned_data)
                    return render(request, 'app/login.html', {
                        'message': 'Cuenta creada satisfactoriamente', 'form': form, })
                except IntegrityError:
                    return render(request,'app/signup.html',{'message':'El usuario ya esta en uso',  'form':form})
                except KeyError as e:
                    return render(request, 'app/signup.html', {'message': e.args[0], 'form': form})
        else:
            form = LoginForm()
        return render(request, 'app/login.html', {'form': form, })


class EditAccount(View):
    choices = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.choices.append(actualizar_atributo(FormasDePago,'metodo'))
 #       self.choices = []
  #      for i in FormasDePago.objects.all().values():
   #         self.choices.append((i['metodo'], i['metodo']))

    def get(self, request):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('index'))
        user = Usuario.objects.get(user=request.user)
        initial = {'first_name': request.user.first_name, 'last_name': request.user.last_name}
        data = {'user': user}
        if user.tipo == 2:
            ven = VendedorFijo.objects.get(usuario=user)
            initial['hora_ini'] = ven.hora_ini
            initial['hora_fin'] = ven.hora_fin

        if user.tipo >= 2:
            vendor = Vendedor.objects.get(usuario=user)
            data['vendor'] = vendor
            pay = vendor.formas_pago.values()
            payment = [i['metodo'] for i in pay]
            initial['formas_pago'] = payment

        form = EditarCuenta(initial=initial)
        form.fields['formas_pago'].choices = self.choices
        data['form'] = form
        return render(request, 'app/edit_account.html', data)

    def post(self, request):
        form = EditarCuenta(request.POST, request.FILES)
        form.fields['formas_pago'].choices = self.choices
        if not request.user.is_authenticated() or not form.is_valid():
            return self.get(request)
        user = Usuario.objects.get(user=request.user)
        user.user.first_name = form.cleaned_data['first_name']
        user.user.last_name = form.cleaned_data['last_name']
        if form.cleaned_data['avatar'] is not None:
            user.avatar = form.cleaned_data['avatar']
        user.save()
        try:
            vendor = Vendedor.objects.get(usuario=user)
            pay = form.cleaned_data['formas_pago']
            vendor.formas_pago.clear()
            for i in pay:
                vendor.formas_pago.add(FormasDePago.objects.get(metodo=i))
            vendor.save()
            svendor = VendedorFijo.objects.get(usuario=user)
            svendor.hora_ini = form.cleaned_data['hora_ini']
            svendor.hora_fin = form.cleaned_data['hora_fin']
            svendor.save()
        finally:
            return HttpResponseRedirect('home')


class EditProduct(View):
    @staticmethod
    def get(request, pid):
        try:
            user = Usuario.objects.get(user=request.user)
            vendor = Vendedor.objects.get(usuario=user)
            products = Producto.objects.filter(vendedor=vendor)
            product = products.get(id=pid)
            initial = {'nombre': product.nombre, 'precio': product.precio,
                       'stock': product.stock, 'descripcion': product.descripcion}
            form = EditarProductoForm(initial=initial)
            return render(request, 'app/edit_product.html', {'form': form, 'user': user,
                                                             'vendor': vendor, 'product': product})
        except:
            return HttpResponseRedirect(reverse('home'))

    def post(self, request, pid):
        try:
            user = Usuario.objects.get(user=request.user)
            vendor = Vendedor.objects.get(usuario=user)
            products = Producto.objects.filter(vendedor=vendor)
            product = products.get(id=pid)
            form = EditarProductoForm(request.POST, request.FILES)
            if not form.is_valid():
                return self.get(request, pid)
            product.nombre = form.cleaned_data['nombre']
            product.precio = form.cleaned_data['precio']
            product.stock = form.cleaned_data['stock']
            product.descripcion = form.cleaned_data['descripcion']
            if form.cleaned_data['imagen'] is not None:
                product.imagen = form.cleaned_data['imagen']
            product.save()
        finally:
            return HttpResponseRedirect(reverse('home'))


def vendor_info(request, pid):
    try:
        user = None
        is_fav = False
        vendor = Vendedor.objects.get(id=pid)
        update(vendor)
        products = []
        raw_products = Producto.objects.filter(vendedor=vendor)
        schedule = VendedorFijo.objects.get(usuario=vendor.usuario).schedule() if vendor.usuario.tipo == 2 else None
        for p in raw_products:
            products.append(p)
        try:
            user = Usuario.objects.get(user=request.user)
            buyer = Alumno.objects.get(usuario=user)
            if buyer.favorites.filter(usuario=vendor.usuario).values().count() != 0:
                is_fav = True
        finally:
            return render(request, 'app/vendor_info.html', {'user': user, 'vendor': vendor,
                                                            'products': products, 'schedule': schedule,
                                                            'is_fav': is_fav})
    except:
        return HttpResponseRedirect(reverse('home'))


def update(ven):
    t = datetime.datetime.now().time()
    if ven.usuario.tipo == 2:
        vendor = VendedorFijo.objects.get(usuario=ven.usuario)
        now = datetime.time(hour=t.hour, minute=t.minute)
        if vendor.hora_ini <= now <= vendor.hora_fin and not vendor.activo:
            vendor.activo = True
        if not vendor.hora_ini <= now <= vendor.hora_fin and vendor.activo:
            vendor.activo = False
        vendor.save()


def like(request):
    try:
        data = {'is_fav_now': False}
        pid = request.POST.get('id', None)
        vendor = Vendedor.objects.get(id=pid)
        buyer = Alumno.objects.get(usuario=Usuario.objects.get(user=request.user))
        if buyer.favorites.filter(usuario=vendor.usuario).values().count() != 0:
            buyer.favorites.remove(vendor)
            vendor.numero_favoritos -= 1
            data['is_fav_now'] = False
        else:
            buyer.favorites.add(vendor)
            vendor.numero_favoritos += 1
            data['is_fav_now'] = True
        buyer.save()
        vendor.save()
        data['favorites'] = vendor.numero_favoritos
        return JsonResponse(data)
    except:
        return HttpResponseRedirect(reverse('home'))


def check_in(request):
    user = Usuario.objects.get(user=request.user)
    vendor = Vendedor.objects.get(usuario=user)

    vendor.activo = True if not vendor.activo else False
    vendor.save()

    return JsonResponse({
        'is_active': vendor.activo
    })


def delete_product(request):
    pid = request.POST.get('id')
    Producto.objects.get(id=pid).delete()
    time.sleep(100)
    return JsonResponse({'success': True})


def delete_account(request):
    user = Usuario.objects.get(user=request.user).user
    auth.logout(request)
    user.delete()
    return JsonResponse({'success': True})
